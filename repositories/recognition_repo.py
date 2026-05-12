import os
import shutil
import logging
from fastapi import UploadFile
from deepface import DeepFace
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
from models.recognition import RecognitionResponse
from services.db import get_connection
from services.s3_utils import download_student_folder
from services.settings_service import get_settings_service
from services.face_embeddings import (
    ensure_embeddings_table,
    extract_embedding_from_image,
    upsert_student_embedding,
    load_enrolled_embeddings,
    cosine_similarity,
    similarity_threshold_from_distance_threshold,
    parse_embedding_json,
)

LOG = logging.getLogger(__name__)
MANILA_TZ = ZoneInfo("Asia/Manila")


class RecognitionRepository:
    def __init__(self):
        self.settings = get_settings_service()

    def _is_postgres(self) -> bool:
        database_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
        return bool(database_url) and not database_url.startswith('sqlite')

    def _db_timestamp_value(self, local_dt: datetime):
        # attendance_logs.timestamp is a plain timestamp in both SQLite and Postgres.
        # Store Manila wall time consistently so date filters do not drift by timezone.
        manila_dt = local_dt.astimezone(MANILA_TZ)
        if self._is_postgres():
            return manila_dt.replace(tzinfo=None)
        return manila_dt.strftime("%Y-%m-%d %H:%M:%S")

    def _parse_db_timestamp(self, value):
        if isinstance(value, datetime):
            return value

        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        normalized = text.replace("T", " ")
        candidates = [normalized]

        if "+" in normalized[10:] or "-" in normalized[10:]:
            try:
                candidates.append(normalized.rsplit(":", 1)[0] + normalized[-3:])
            except Exception:
                pass

        for candidate in candidates:
            for fmt in (
                "%Y-%m-%d %H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ):
                try:
                    parsed = datetime.strptime(candidate, fmt)
                    if parsed.tzinfo is None:
                        return parsed.replace(tzinfo=MANILA_TZ)
                    return parsed
                except ValueError:
                    continue

        try:
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=MANILA_TZ)
            return parsed
        except Exception:
            LOG.warning("Could not parse attendance timestamp value: %s", value)
            return None

    def _build_attendance_response(self, cursor, conn, student_id: int, class_id: int) -> RecognitionResponse:
        cursor.execute('''
            SELECT day_of_week, start_time, end_time FROM classes WHERE class_id = ?
        ''', (class_id,))
        class_row = cursor.fetchone()
        if not class_row:
            print(f"[DEBUG] No class details found for class_id={class_id}")
            return RecognitionResponse(status="failed", message="Class schedule not found for selected class")
        day_of_week, start_time_val, end_time_val = class_row

        # Normalize start/end times: DB may return time objects or strings
        def _to_time_str(val):
            if isinstance(val, str):
                return val
            try:
                if isinstance(val, dt_time):
                    return val.strftime("%H:%M")
            except Exception:
                pass
            return str(val)

        start_time_str = _to_time_str(start_time_val)
        end_time_str = _to_time_str(end_time_val)

        now = datetime.now(MANILA_TZ)
        timestamp_value = self._db_timestamp_value(now)
        attendance_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")

        if current_day != day_of_week:
            print(f"[DEBUG] Not class day: today={current_day}, class_day={day_of_week}")
            return RecognitionResponse(
                status="failed",
                message=f"Attendance recognition time not valid: class is scheduled on {day_of_week}"
            )

        try:
            class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=MANILA_TZ)
            class_end = datetime.strptime(attendance_date + ' ' + end_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=MANILA_TZ)
        except ValueError:
            try:
                class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %I:%M%p").replace(tzinfo=MANILA_TZ)
                class_end = datetime.strptime(attendance_date + ' ' + end_time_str, "%Y-%m-%d %I:%M%p").replace(tzinfo=MANILA_TZ)
            except Exception as e:
                print(f"[DEBUG] Could not parse start_time or end_time: {e}")
                return RecognitionResponse(
                    status="error",
                    message="Invalid class schedule time format"
                )

        if not (class_start <= now <= class_end):
            print(f"[DEBUG] Outside class hours: now={now}, class_start={class_start}, class_end={class_end}")
            start_label = class_start.strftime("%I:%M %p").lstrip("0")
            end_label = class_end.strftime("%I:%M %p").lstrip("0")
            return RecognitionResponse(
                status="failed",
                message=f"Attendance recognition time not valid: no active class schedule right now ({start_label} - {end_label})"
            )

        delta = (now - class_start).total_seconds() / 60.0
        late_threshold = self.settings.late_threshold_minutes
        absent_threshold = self.settings.absent_threshold_minutes

        if 0 <= delta <= late_threshold:
            status_name = "Present"
            print(f"[DEBUG] Marked as Present: delta={delta:.2f} mins since class start (<= {late_threshold} mins)")
        elif late_threshold < delta <= absent_threshold:
            status_name = "Late"
            print(f"[DEBUG] Marked as Late: delta={delta:.2f} mins since class start ({late_threshold}-{absent_threshold} mins)")
        else:
            status_name = "Absent"
            print(f"[DEBUG] Marked as Absent: delta={delta:.2f} mins since class start (> {absent_threshold} mins)")

        cursor.execute('''
            SELECT status_id FROM attendance_status_types WHERE status_name = ?
        ''', (status_name,))
        status_row = cursor.fetchone()
        if not status_row:
            print(f"[DEBUG] No status_id found for status_name={status_name}")
            return RecognitionResponse(status="error", message=f"Attendance status mapping not found for {status_name}")
        status_id = status_row[0]

        cursor.execute('''
            SELECT last_name FROM students WHERE student_id = ?
        ''', (student_id,))
        name_row = cursor.fetchone()
        student_name = name_row[0] if name_row else "Unknown"

        if self._is_postgres():
            cursor.execute("""
                SELECT timestamp FROM attendance_logs
                WHERE student_id = ? AND class_id = ?
                AND timestamp::date = ?::date
                ORDER BY timestamp DESC LIMIT 1
            """, (student_id, class_id, attendance_date))
        else:
            cursor.execute("""
                SELECT timestamp FROM attendance_logs
                WHERE student_id = ? AND class_id = ?
                AND DATE(timestamp) = DATE(?)
                ORDER BY timestamp DESC LIMIT 1
            """, (student_id, class_id, attendance_date))
        last_attendance_row = cursor.fetchone()
        buffer_minutes = self.settings.attendance_buffer_minutes

        if last_attendance_row is None:
            should_insert = True
            print(f"[DEBUG] No previous attendance for student {student_id} in class {class_id} today")
        else:
            last_timestamp = self._parse_db_timestamp(last_attendance_row[0])
            if last_timestamp is None:
                should_insert = True
                print("[DEBUG] Unparseable previous attendance timestamp; allowing insert")
            else:
                if last_timestamp.tzinfo:
                    now_ref = now.astimezone(last_timestamp.tzinfo)
                else:
                    now_ref = now.replace(tzinfo=None)
                time_diff = (now_ref - last_timestamp).total_seconds() / 60.0
                if time_diff < buffer_minutes:
                    should_insert = False
                    print(f"[DEBUG] Duplicate attendance blocked: last check-in {time_diff:.2f} mins ago (< {buffer_minutes} mins buffer)")
                else:
                    should_insert = True
                    print(f"[DEBUG] Allowing attendance: {time_diff:.2f} mins since last check-in (>= {buffer_minutes} mins buffer)")

        recorded = False
        if should_insert:
            note = f"Face recognized at {now.strftime('%H:%M:%S')} - {status_name}"
            cursor.execute("""
                INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, class_id, timestamp_value, status_id, note))
            conn.commit()
            print(f"[DEBUG] Attendance logged for student {student_id} in class {class_id}")
            recorded = True
        else:
            note = None
            recorded = False

        message = None
        if not recorded:
            message = f"Attendance already recorded within the last {buffer_minutes} minutes."
            print(f"[DEBUG] Duplicate attendance not inserted for student {student_id} in class {class_id}")

        return RecognitionResponse(
            status="success",
            student_id=str(student_id),
            student_name=student_name,
            attendance_status=status_name,
            attendance_recorded=recorded,
            message=message
        )

    async def recognize_face(self, file: UploadFile, class_id: int) -> RecognitionResponse:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                ensure_embeddings_table(cursor)

                model_name = self.settings.face_recognition_model
                threshold = self.settings.recognition_threshold
                enforce_detection = False

                # 1) Embedding-first recognition from DB
                query_embedding = extract_embedding_from_image(
                    image_path=temp_path,
                    model_name=model_name,
                    enforce_detection=enforce_detection,
                )

                if query_embedding:
                    enrolled_embeddings = load_enrolled_embeddings(
                        cursor=cursor,
                        class_id=class_id,
                        model_name=model_name,
                    )
                    print(f"[DEBUG] Loaded {len(enrolled_embeddings)} stored embeddings for class {class_id}")

                    similarity_threshold = similarity_threshold_from_distance_threshold(threshold)
                    best_student_id = None
                    best_similarity = -1.0

                    for candidate_student_id, _, embedding_json in enrolled_embeddings:
                        candidate_embedding = parse_embedding_json(embedding_json)
                        if not candidate_embedding:
                            continue
                        sim = cosine_similarity(query_embedding, candidate_embedding)
                        if sim > best_similarity:
                            best_similarity = sim
                            best_student_id = candidate_student_id

                    print(f"[DEBUG] Best embedding match: student_id={best_student_id}, similarity={best_similarity:.4f}, threshold={similarity_threshold:.4f}")
                    if best_student_id is not None and best_similarity >= similarity_threshold:
                        response = self._build_attendance_response(cursor, conn, best_student_id, class_id)
                        if response.status == "success" and response.attendance_recorded:
                            upsert_student_embedding(
                                cursor=cursor,
                                student_id=best_student_id,
                                model_name=model_name,
                                embedding=query_embedding,
                                source_image_path=temp_path,
                            )
                            conn.commit()
                        return response

                # 2) Fallback: image-to-image verify (legacy path)
                # Get all students enrolled in this class
                cursor.execute('''
                    SELECT e.student_id, s.student_number, s.face_data_path 
                    FROM enrollments e
                    JOIN students s ON e.student_id = s.student_id
                    WHERE e.class_id = ?
                ''', (class_id,))
                enrolled_students = cursor.fetchall()
                print(f"[DEBUG] Enrolled students in class {class_id}: {enrolled_students}")

                student_faces = {}
                use_s3 = os.getenv('USE_S3', '0').lower() in ('1', 'true', 'yes')
                for student_id, student_number, face_data_path in enrolled_students:
                    # Use the face_data_path from the database, or construct it
                    if face_data_path:
                        student_folder = face_data_path
                    else:
                        student_folder = os.path.join("dataset", str(student_number))

                    # Check if folder exists locally
                    if os.path.isdir(student_folder):
                        images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith('.jpg')]
                    elif use_s3:
                        # Optional S3 fallback if explicitly enabled
                        tmpdir = os.path.join("/tmp", f"dataset_{student_number}") if os.name != 'nt' else os.path.join("C:\\Windows\\Temp", f"dataset_{student_number}")
                        os.makedirs(tmpdir, exist_ok=True)
                        try:
                            download_student_folder('fras-data', f'dataset/{student_number}/', tmpdir)
                            images = [os.path.join(tmpdir, img) for img in os.listdir(tmpdir) if img.lower().endswith('.jpg')]
                        except Exception:
                            images = []
                    else:
                        images = []

                    if images:
                        student_faces[student_id] = images[0]  # Use first image for comparison

                print(f"[DEBUG] Student faces to compare: {student_faces}")

                # Sort by student_id for consistent matching order (prevents random mismatches)
                sorted_student_faces = sorted(student_faces.items(), key=lambda x: x[0])

                # Compare faces
                for student_id, img_path in sorted_student_faces:
                    try:
                        print(f"[DEBUG] Comparing temp image {temp_path} with {img_path} for student {student_id}")

                        result = DeepFace.verify(
                            img1_path=temp_path,
                            img2_path=img_path,
                            model_name=model_name,
                            enforce_detection=enforce_detection,
                            threshold=threshold
                        )
                        print(f"[DEBUG] DeepFace result for {student_id}: {result}")
                        if result["verified"]:
                            if query_embedding:
                                upsert_student_embedding(
                                    cursor=cursor,
                                    student_id=student_id,
                                    model_name=model_name,
                                    embedding=query_embedding,
                                    source_image_path=temp_path,
                                )
                                conn.commit()
                            response = self._build_attendance_response(cursor, conn, student_id, class_id)
                            return response
                    except Exception as e:
                        print(f"[DEBUG] Exception for {student_id}: {e}")
                        continue
        except Exception as e:
            LOG.exception("Unhandled exception during face recognition")
            return RecognitionResponse(status="error", message="Internal server error")
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

        LOG.debug("Returning failure response: No match found")
        return RecognitionResponse(status="failed", message="No match found")

    async def mark_absents(self, class_id: int, date: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all enrolled students for the class
            cursor.execute('''
                SELECT e.student_id, s.last_name
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.class_id = ?
            ''', (class_id,))
            enrolled_students = cursor.fetchall()
            
            # Get students who already have attendance for the date
            if self._is_postgres():
                cursor.execute('''
                    SELECT DISTINCT student_id FROM attendance_logs
                    WHERE class_id = ?
                    AND timestamp::date = ?::date
                ''', (class_id, date))
            else:
                cursor.execute('''
                    SELECT DISTINCT student_id FROM attendance_logs
                    WHERE class_id = ? AND DATE(timestamp) = DATE(?)
                ''', (class_id, date))
            attended_students = {row[0] for row in cursor.fetchall()}
            
            # Get absent status_id
            cursor.execute('''
                SELECT status_id FROM attendance_status_types WHERE status_name = 'Absent'
            ''')
            status_row = cursor.fetchone()
            if not status_row:
                return {"error": "Absent status not found"}
            absent_status_id = status_row[0]
            
            absent_count = 0
            for student_id, last_name in enrolled_students:
                if student_id not in attended_students:
                    # Insert absent record
                    timestamp_local = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=MANILA_TZ)
                    timestamp = self._db_timestamp_value(timestamp_local)
                    note = f"Auto-marked absent on {date} - No attendance recorded during class"
                    cursor.execute('''
                        INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (student_id, class_id, timestamp, absent_status_id, note))
                    absent_count += 1
                    print(f"[DEBUG] Marked student {student_id} ({last_name}) as Absent for class {class_id} on {date}")
            
            conn.commit()
            return {"message": f"Marked {absent_count} students as absent for class {class_id} on {date}"}


def get_recognition_repository():
    return RecognitionRepository()
