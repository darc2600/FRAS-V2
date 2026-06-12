from __future__ import annotations

import os
import shutil
import tempfile
from datetime import date, datetime, time, timedelta
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import UploadFile
from fastapi import HTTPException

from services.face_embeddings import (
    cosine_similarity,
    ensure_embeddings_table,
    extract_embeddings_from_image,
    load_active_enrolled_embeddings,
    parse_embedding_json,
    similarity_threshold_from_distance_threshold,
    upsert_student_embedding,
)
from services.settings_service import get_settings_service
from services.db import get_connection
from v2.models import (
    V2AttendanceEvent,
    V2BreakUnlockRequest,
    V2ClassCard,
    V2ClassRosterContext,
    V2ClassRosterHistoryItem,
    V2ClassRosterResponse,
    V2ClassRosterStudent,
    V2CreateEventRequest,
    V2FaceProfileContextResponse,
    V2FaceProfileSaveResponse,
    V2ManualAttendanceRequest,
    V2ProfessorScheduleClass,
    V2ProfessorScheduleResponse,
    V2ProfessorSummary,
    V2RecognitionMatchResponse,
    V2ReviewSummary,
    V2SessionHistoryClassContext,
    V2SessionHistoryResponse,
    V2SessionHistoryRow,
    V2SessionHistorySummary,
    V2SessionDetailResponse,
    V2SessionResponse,
    V2SessionReviewResponse,
    V2StartSessionRequest,
    V2StudentClassHistoryHeader,
    V2StudentClassHistoryResponse,
    V2StudentClassHistoryRow,
    V2StudentClassHistorySummary,
    V2StudentRecord,
    V2TodayClassesResponse,
)
from v2.repository import V2AttendanceRepository
from api.auth import verify_user_password


MANILA_TZ = ZoneInfo("Asia/Manila")
LOG = logging.getLogger(__name__)
V2_MIN_RECOGNITION_SIMILARITY = float(os.getenv("FRAS_V2_FACE_SIMILARITY_THRESHOLD", "0.70"))
V2_RECOGNITION_MARGIN = float(os.getenv("FRAS_V2_FACE_MATCH_MARGIN", "0.07"))


class V2AttendanceService:
    def __init__(self, repo: V2AttendanceRepository | None = None):
        self.repo = repo or V2AttendanceRepository()

    def list_professors(self) -> list[V2ProfessorSummary]:
        return [
            V2ProfessorSummary(
                professor_id=row[0],
                user_id=row[1],
                faculty_number=row[2],
                professor_name=f"{row[4]}, {row[3]}",
                email=row[5],
                total_units=row[6],
                lecture_units=row[7],
                lab_units=row[8],
            )
            for row in self.repo.list_professors()
        ]

    def get_today_classes(self, professor_id: int = 1, target_date: date | None = None) -> V2TodayClassesResponse:
        target_date = target_date or datetime.now(MANILA_TZ).date()
        now = datetime.now(MANILA_TZ)
        day_name = target_date.strftime("%A")
        rows = self.repo.list_professor_classes_for_day(professor_id, day_name)

        current: list[V2ClassCard] = []
        upcoming: list[V2ClassCard] = []
        completed: list[V2ClassCard] = []

        for row in rows:
            start_time = self._coerce_time(row[6])
            end_time = self._coerce_time(row[7])
            status = self._class_status(target_date, start_time, end_time, now)
            card = V2ClassCard(
                class_id=row[0],
                course_code=row[1],
                course_name=row[2],
                section=row[3],
                room=row[4] or "TBA",
                day_of_week=row[5],
                start_time=start_time,
                end_time=end_time,
                student_count=row[8],
                status=status,
                active_session_id=row[9],
            )
            if status == "current":
                current.append(card)
            elif status == "upcoming":
                upcoming.append(card)
            else:
                completed.append(card)

        return V2TodayClassesResponse(
            professor_id=professor_id,
            date=target_date,
            current=current,
            upcoming=upcoming,
            completed=completed,
        )

    def get_professor_schedule(self, professor_id: int = 1) -> V2ProfessorScheduleResponse:
        classes = [
            V2ProfessorScheduleClass(
                class_id=row[0],
                course_code=row[1],
                course_name=row[2],
                section=row[3],
                room=row[4] or "TBA",
                day_of_week=row[5],
                start_time=self._coerce_time(row[6]),
                end_time=self._coerce_time(row[7]),
                student_count=row[8],
            )
            for row in self.repo.list_professor_schedule(professor_id)
        ]
        return V2ProfessorScheduleResponse(professor_id=professor_id, classes=classes)

    def get_class_session_history(self, class_id: int) -> V2SessionHistoryResponse:
        context_row = self.repo.get_class_history_context(class_id)
        if not context_row:
            raise HTTPException(status_code=404, detail="Class not found.")

        context = V2SessionHistoryClassContext(
            class_id=context_row[0],
            course_code=context_row[1],
            course_name=context_row[2],
            section=context_row[3],
            room=context_row[4] or "TBA",
            professor_name=f"{context_row[5]}, {context_row[6]}",
        )

        sessions: list[V2SessionHistoryRow] = []
        for row in self.repo.list_class_session_history(class_id):
            total_students = int(row[4] or 0)
            attendance_count = int(row[5] or 0)
            attendance_rate = round((attendance_count / total_students) * 100, 2) if total_students else 0.0
            warning_count = int(row[7] or 0)
            sessions.append(
                V2SessionHistoryRow(
                    session_id=row[0],
                    date=self._coerce_datetime(row[1]).date(),
                    scheduled_start=self._coerce_datetime(row[1]),
                    scheduled_end=self._coerce_datetime(row[2]),
                    attendance_count=attendance_count,
                    total_students=total_students,
                    attendance_rate=attendance_rate,
                    average_presence_minutes=round(float(row[6] or 0)),
                    warning_count=warning_count,
                    excused_count=int(row[8] or 0),
                    status=self._history_status(str(row[3]), warning_count),
                )
            )

        total_sessions = len(sessions)
        summary = V2SessionHistorySummary(
            total_sessions=total_sessions,
            average_attendance_rate=round(sum(item.attendance_rate for item in sessions) / total_sessions, 2) if total_sessions else 0.0,
            average_presence_minutes=round(sum(item.average_presence_minutes for item in sessions) / total_sessions) if total_sessions else 0,
            sessions_requiring_review=sum(1 for item in sessions if item.status == "needs_review"),
            excused_students=sum(item.excused_count for item in sessions),
        )

        return V2SessionHistoryResponse(
            class_context=context,
            summary=summary,
            sessions=sessions,
        )

    def get_professor_session_history(self, professor_id: int) -> V2SessionHistoryResponse:
        context_row = self.repo.get_professor_history_context(professor_id)
        if not context_row:
            raise HTTPException(status_code=404, detail="Professor not found.")

        sessions: list[V2SessionHistoryRow] = []
        for row in self.repo.list_professor_session_history(professor_id):
            total_students = int(row[9] or 0)
            attendance_count = int(row[10] or 0)
            attendance_rate = round((attendance_count / total_students) * 100, 2) if total_students else 0.0
            warning_count = int(row[12] or 0)
            sessions.append(
                V2SessionHistoryRow(
                    session_id=row[0],
                    class_id=row[4],
                    course_code=row[5],
                    course_name=row[6],
                    section=row[7],
                    room=row[8] or "TBA",
                    date=self._coerce_datetime(row[1]).date(),
                    scheduled_start=self._coerce_datetime(row[1]),
                    scheduled_end=self._coerce_datetime(row[2]),
                    attendance_count=attendance_count,
                    total_students=total_students,
                    attendance_rate=attendance_rate,
                    average_presence_minutes=round(float(row[11] or 0)),
                    warning_count=warning_count,
                    excused_count=int(row[13] or 0),
                    status=self._history_status(str(row[3]), warning_count),
                )
            )

        total_sessions = len(sessions)
        summary = V2SessionHistorySummary(
            total_sessions=total_sessions,
            average_attendance_rate=round(sum(item.attendance_rate for item in sessions) / total_sessions, 2) if total_sessions else 0.0,
            average_presence_minutes=round(sum(item.average_presence_minutes for item in sessions) / total_sessions) if total_sessions else 0,
            sessions_requiring_review=sum(1 for item in sessions if item.status == "needs_review"),
            excused_students=sum(item.excused_count for item in sessions),
        )

        return V2SessionHistoryResponse(
            class_context=None,
            summary=summary,
            sessions=sessions,
        )

    def get_class_roster(self, class_id: int) -> V2ClassRosterResponse:
        context_row = self.repo.get_class_roster_context(class_id)
        if not context_row:
            raise HTTPException(status_code=404, detail="Class not found.")

        context = V2ClassRosterContext(
            class_id=context_row[0],
            course_code=context_row[1],
            course_name=context_row[2],
            section=context_row[3],
            room=context_row[4] or "TBA",
            professor_name=f"{context_row[5]}, {context_row[6]}",
            student_count=int(context_row[7] or 0),
        )

        students: list[V2ClassRosterStudent] = []
        for row in self.repo.list_class_roster_students(class_id):
            student_id = int(row[0])
            total_sessions = int(row[7] or 0)
            present_sessions = int(row[8] or 0)
            late_sessions = int(row[9] or 0)
            partial_sessions = int(row[10] or 0)
            absent_sessions = int(row[11] or 0)
            excused_sessions = int(row[12] or 0)
            attended_sessions = present_sessions + late_sessions + excused_sessions
            last_face_update = self._coerce_datetime(row[5]) if row[5] else None
            recognition_confidence = float(row[13]) if row[13] is not None else None
            last_recognition_at = self._coerce_datetime(row[14]) if row[14] else None

            students.append(
                V2ClassRosterStudent(
                    student_id=student_id,
                    student_number=row[1],
                    student_name=f"{row[3]}, {row[2]}",
                    email=row[4],
                    face_profile_status=self._face_profile_status(int(row[6] or 0), last_face_update),
                    recognition_status=self._recognition_status(int(row[6] or 0), recognition_confidence, last_recognition_at),
                    attendance_rate=round((attended_sessions / total_sessions) * 100, 2) if total_sessions else 0.0,
                    last_face_update=last_face_update,
                    recognition_confidence=recognition_confidence,
                    total_sessions=total_sessions,
                    present_sessions=present_sessions,
                    late_sessions=late_sessions,
                    partial_sessions=partial_sessions,
                    absent_sessions=absent_sessions,
                    excused_sessions=excused_sessions,
                    recent_history=self._get_class_student_history(class_id, student_id),
                )
            )

        return V2ClassRosterResponse(class_context=context, students=students)

    def get_student_class_history(self, class_id: int, student_id: int) -> V2StudentClassHistoryResponse:
        header_row = self.repo.get_student_class_history_header(class_id, student_id)
        if not header_row:
            raise HTTPException(status_code=404, detail="Student is not enrolled in this class.")

        records: list[V2StudentClassHistoryRow] = []
        present = late = partial = absent = excused = 0
        for row in self.repo.list_student_class_history_records(class_id, student_id):
            status = str(row[3])
            if status == "present":
                present += 1
            elif status == "late":
                late += 1
            elif status == "partial":
                absent += 1
            elif status == "excused":
                excused += 1
            else:
                absent += 1

            scheduled_start = self._coerce_datetime(row[1])
            records.append(
                V2StudentClassHistoryRow(
                    session_id=row[0],
                    session_date=scheduled_start.date(),
                    scheduled_start=scheduled_start,
                    scheduled_end=self._coerce_datetime(row[2]),
                    attendance_status=status,
                    presence_duration_minutes=int(row[4] or 0),
                    outside_duration_minutes=int(row[5] or 0),
                    break_count=int(row[6] or 0),
                    system_assessment=str(row[7] or "absent"),
                )
            )

        total = len(records)
        attended = present + late + excused
        attendance_rate = round((attended / total) * 100, 2) if total else 0.0
        header = V2StudentClassHistoryHeader(
            class_id=header_row[0],
            student_id=header_row[1],
            student_number=header_row[2],
            student_name=f"{header_row[4]}, {header_row[3]}",
            course_code=header_row[5],
            course_name=header_row[6],
            section=header_row[7],
            room=header_row[8] or "TBA",
            attendance_rate=attendance_rate,
        )
        summary = V2StudentClassHistorySummary(
            total_sessions=total,
            present_sessions=present,
            late_sessions=late,
            partial_sessions=partial,
            absent_sessions=absent,
            excused_sessions=excused,
            attendance_rate=attendance_rate,
        )
        return V2StudentClassHistoryResponse(header=header, summary=summary, records=records)

    def get_face_profile_context(self, class_id: int, student_id: int) -> V2FaceProfileContextResponse:
        row = self.repo.get_face_profile_context(class_id, student_id)
        if not row:
            raise HTTPException(status_code=404, detail="Student is not enrolled in this class.")

        last_face_update = self._coerce_datetime(row[9]) if row[9] else None
        return V2FaceProfileContextResponse(
            class_id=row[0],
            student_id=row[1],
            student_number=row[2],
            student_name=f"{row[4]}, {row[3]}",
            course_code=row[5],
            course_name=row[6],
            section=row[7],
            room=row[8] or "TBA",
            face_profile_status=self._face_profile_status(int(row[10] or 0), last_face_update),
            last_face_update=last_face_update,
        )

    async def recognize_face_for_class(self, class_id: int, image: UploadFile) -> V2RecognitionMatchResponse:
        if not self.repo.get_class_roster_context(class_id):
            raise HTTPException(status_code=404, detail="Class not found.")

        suffix = Path(image.filename or "frame.jpg").suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                shutil.copyfileobj(image.file, temp_file)
                temp_path = temp_file.name

            settings = get_settings_service()
            model_name = settings.face_recognition_model
            configured_threshold = self._v2_similarity_threshold(settings.recognition_threshold)
            query_embeddings = extract_embeddings_from_image(
                temp_path,
                model_name=model_name,
                enforce_detection=True,
            )
            detected_face_count = len(query_embeddings)
            query_embedding = query_embeddings[0] if query_embeddings else None
            if not query_embedding:
                LOG.info(
                    "V2 recognition no_face_recognized class_id=%s detected_face_count=%s threshold=%.4f",
                    class_id,
                    detected_face_count,
                    configured_threshold,
                )
                return V2RecognitionMatchResponse(
                    status="no_face_recognized",
                    decision_result="no_face_recognized",
                    message="No face recognized in the frame.",
                    detected_face_count=detected_face_count,
                    recognition_threshold=round(configured_threshold, 4),
                    match_margin=round(V2_RECOGNITION_MARGIN, 4),
                )

            with get_connection() as conn:
                cursor = conn.cursor()
                ensure_embeddings_table(cursor)
                enrolled_embeddings = load_active_enrolled_embeddings(cursor, class_id=class_id, model_name=model_name)

            candidates = []
            for embedding_id, candidate_student_id, first_name, last_name, embedding_json, source_image_path, profile_id in enrolled_embeddings:
                candidate_embedding = parse_embedding_json(embedding_json)
                if not candidate_embedding:
                    continue
                similarity = cosine_similarity(query_embedding, candidate_embedding)
                candidates.append({
                    "embedding_id": int(embedding_id),
                    "student_id": int(candidate_student_id),
                    "student_name": f"{last_name}, {first_name}",
                    "similarity": similarity,
                    "source_image_path": source_image_path,
                    "profile_id": int(profile_id) if profile_id is not None else None,
                })

            candidates.sort(key=lambda item: item["similarity"], reverse=True)
            decision = self._decide_recognition_match(candidates, configured_threshold, V2_RECOGNITION_MARGIN)
            best = decision["best"]
            second = decision["second"]

            if not best:
                LOG.info(
                    "V2 recognition failed_no_profiles class_id=%s detected_face_count=%s threshold=%.4f",
                    class_id,
                    detected_face_count,
                    configured_threshold,
                )
                return V2RecognitionMatchResponse(
                    status="failed",
                    decision_result="no_enrolled_profiles",
                    message="No enrolled face profiles are available for this class.",
                    detected_face_count=detected_face_count,
                    recognition_threshold=round(configured_threshold, 4),
                    match_margin=round(V2_RECOGNITION_MARGIN, 4),
                )

            common = {
                "detected_face_count": detected_face_count,
                "confidence": self._confidence_percent(float(best["similarity"])),
                "best_match_score": round(float(best["similarity"]), 4),
                "second_best_match_score": round(float(second["similarity"]), 4) if second else None,
                "recognition_threshold": round(configured_threshold, 4),
                "match_margin": round(V2_RECOGNITION_MARGIN, 4),
                "matched_embedding_id": best["embedding_id"],
                "matched_profile_id": best["profile_id"],
            }

            if decision["result"] == "below_threshold":
                LOG.info(
                    "V2 recognition below_threshold class_id=%s best_student_id=%s best=%.4f second=%s threshold=%.4f margin=%.4f embedding_id=%s profile_id=%s faces=%s",
                    class_id,
                    best["student_id"],
                    best["similarity"],
                    f"{second['similarity']:.4f}" if second else None,
                    configured_threshold,
                    V2_RECOGNITION_MARGIN,
                    best["embedding_id"],
                    best["profile_id"],
                    detected_face_count,
                )
                return V2RecognitionMatchResponse(
                    status="below_threshold",
                    decision_result="below_threshold",
                    message="No confident student match found.",
                    **common,
                )

            if decision["result"] == "ambiguous_match":
                LOG.warning(
                    "V2 recognition ambiguous_match class_id=%s best_student_id=%s second_student_id=%s best=%.4f second=%.4f threshold=%.4f margin=%.4f embedding_id=%s profile_id=%s faces=%s",
                    class_id,
                    best["student_id"],
                    second["student_id"] if second else None,
                    best["similarity"],
                    second["similarity"] if second else -1.0,
                    configured_threshold,
                    V2_RECOGNITION_MARGIN,
                    best["embedding_id"],
                    best["profile_id"],
                    detected_face_count,
                )
                return V2RecognitionMatchResponse(
                    status="ambiguous_match",
                    decision_result="ambiguous_match",
                    message="Face match is ambiguous. Please use manual review or recapture.",
                    student_id=int(best["student_id"]),
                    student_name=str(best["student_name"]),
                    **common,
                )

            best_student_id = int(best["student_id"])
            student = self.repo.get_student_name_for_class(class_id, best_student_id)
            if not student:
                return V2RecognitionMatchResponse(
                    status="failed",
                    decision_result="matched_student_not_enrolled",
                    message="Matched student is not enrolled in this class.",
                    student_id=best_student_id,
                    student_name=str(best["student_name"]),
                    **common,
                )

            LOG.info(
                "V2 recognition recognized class_id=%s student_id=%s best=%.4f second=%s threshold=%.4f margin=%.4f embedding_id=%s profile_id=%s faces=%s",
                class_id,
                best_student_id,
                best["similarity"],
                f"{second['similarity']:.4f}" if second else None,
                configured_threshold,
                V2_RECOGNITION_MARGIN,
                best["embedding_id"],
                best["profile_id"],
                detected_face_count,
            )
            return V2RecognitionMatchResponse(
                status="success",
                decision_result="recognized",
                student_id=best_student_id,
                student_name=f"{student[1]}, {student[0]}",
                message="Student recognized.",
                **common,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Unable to recognize the uploaded frame.") from exc
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    async def save_face_profile(
        self,
        class_id: int,
        student_id: int,
        angles: list[str],
        images: list[UploadFile],
    ) -> V2FaceProfileSaveResponse:
        context = self.get_face_profile_context(class_id, student_id)
        if len(images) != len(angles):
            raise HTTPException(status_code=400, detail="Angles and images must have the same count.")
        if not images:
            raise HTTPException(status_code=400, detail="Capture the front face image before saving.")

        normalized_angles = [angle.strip().lower() for angle in angles]
        if "front" not in normalized_angles:
            raise HTTPException(status_code=400, detail="Front face capture is required.")

        dataset_base = Path(os.getenv("DATASET_PATH", "dataset"))
        safe_student = "".join(ch for ch in context.student_number if ch.isalnum() or ch in ("-", "_"))
        save_dir = dataset_base / "v2_face_profiles" / safe_student / "active"
        save_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: list[str] = []
        for angle, upload in zip(normalized_angles, images):
            extension = Path(upload.filename or "").suffix.lower() or ".jpg"
            if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                extension = ".jpg"
            filename = f"{angle}{extension}"
            path = save_dir / filename
            content = await upload.read()
            path.write_bytes(content)
            saved_paths.append(str(path))

        front_index = normalized_angles.index("front")
        front_path = saved_paths[front_index]
        settings = get_settings_service()
        model_name = settings.face_recognition_model
        face_embeddings = extract_embeddings_from_image(front_path, model_name=model_name, enforce_detection=True)
        if len(face_embeddings) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple faces were detected in the capture. Please retake with only the selected student in frame.",
            )
        embedding = face_embeddings[0] if face_embeddings else None
        if not embedding:
            raise HTTPException(
                status_code=400,
                detail="No face was detected in the front capture. Please retake the face profile image.",
            )

        self.repo.replace_student_face_profile(
            student_id=student_id,
            face_image_path=front_path,
            embedding_json=None,
            model_name=None,
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            ensure_embeddings_table(cursor)
            upsert_student_embedding(
                cursor=cursor,
                student_id=student_id,
                model_name=model_name,
                embedding=embedding,
                source_image_path=front_path,
            )

        return V2FaceProfileSaveResponse(
            status="success",
            message="Face profile saved successfully.",
            student_id=student_id,
            face_profile_status="registered",
            saved_angles=normalized_angles,
            image_paths=saved_paths,
        )

    def start_session(self, class_id: int, payload: V2StartSessionRequest) -> V2SessionDetailResponse:
        session_date = payload.session_date or datetime.now(MANILA_TZ).date()
        class_row = self.repo.get_class_for_session_start(class_id, payload.professor_id)
        if not class_row:
            raise HTTPException(status_code=404, detail="Class not found for professor.")

        active = self.repo.get_active_session(class_id, payload.professor_id)
        if active:
            return self.get_session_detail(active[0])

        start_time = self._coerce_time(class_row[3])
        end_time = self._coerce_time(class_row[4])
        scheduled_start = self._combine_local(session_date, start_time)
        scheduled_end = self._combine_local(session_date, end_time)
        actual_start = datetime.now(MANILA_TZ).replace(tzinfo=None)

        session_id = self.repo.create_session(
            class_id=class_id,
            professor_id=payload.professor_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            actual_start=actual_start,
        )
        return self.get_session_detail(session_id)

    def get_session_detail(self, session_id: int) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        return V2SessionDetailResponse(
            session=session,
            roster=self._get_roster(session_id),
            events=self._get_events(session_id),
        )

    def get_session_review(self, session_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        roster = self._get_roster(session_id)
        summary = self._build_review_summary(roster)
        return V2SessionReviewResponse(session=session, summary=summary, roster=roster)

    def create_event(self, session_id: int, payload: V2CreateEventRequest) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status not in {"in_progress", "on_break", "under_review"}:
            raise HTTPException(status_code=400, detail="Session is not accepting attendance events.")
        if session.session_status == "on_break":
            if payload.event_type != "break_in" or payload.event_source != "facial_recognition":
                raise HTTPException(status_code=423, detail="Session Break is active. Only facial-recognition Break In return detection is allowed.")

        record_row = self.repo.get_record_for_student(session_id, payload.student_id)
        if not record_row:
            raise HTTPException(status_code=404, detail="Student is not enrolled in this session.")

        event_time = payload.event_time or datetime.now(MANILA_TZ).replace(tzinfo=None)
        record_id = int(record_row[0])
        if payload.event_source == "facial_recognition" and payload.event_type in {"time_in", "break_in"}:
            recent_window_start = event_time.replace(tzinfo=None) - timedelta(seconds=30)
            if self.repo.get_recent_student_event(session_id, payload.student_id, payload.event_type, recent_window_start):
                LOG.info(
                    "V2 duplicate recognition event blocked session_id=%s student_id=%s event_type=%s",
                    session_id,
                    payload.student_id,
                    payload.event_type,
                )
                return self.get_session_detail(session_id)
        if session.session_status == "on_break":
            last_event = self.repo.get_student_events(session_id, payload.student_id)[-1:]
            if not last_event or last_event[0][0] != "break_out":
                raise HTTPException(
                    status_code=409,
                    detail="Return Detection Mode only accepts Break In for students currently out on break.",
                )

        self.repo.create_event(
            session_id=session_id,
            record_id=record_id,
            student_id=payload.student_id,
            event_type=payload.event_type,
            event_time=event_time,
            event_source=payload.event_source,
            recognition_confidence=payload.recognition_confidence,
            notes=payload.notes,
        )
        self._recalculate_student_record(session, record_id, payload.student_id)
        return self.get_session_detail(session_id)

    def save_manual_attendance(self, session_id: int, payload: V2ManualAttendanceRequest) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "finalized":
            raise HTTPException(status_code=400, detail="Finalized sessions cannot be changed.")
        if session.session_status == "on_break":
            raise HTTPException(status_code=423, detail="Session Break is active. Manual attendance is locked until the professor ends break.")
        if session.session_status not in {"in_progress", "on_break", "under_review"}:
            raise HTTPException(status_code=400, detail="Session is not accepting manual attendance.")

        now = datetime.now(MANILA_TZ).replace(tzinfo=None)
        for item in payload.records:
            record_row = self.repo.get_record_for_override(session_id, item.record_id, item.student_id)
            if not record_row:
                raise HTTPException(status_code=404, detail="Student record not found for this session.")

            previous_status = str(record_row[1])
            existing_time_in = self._coerce_datetime(record_row[2]) if record_row[2] else None
            if item.status in {"present", "late"}:
                assessment = "valid_presence"
                time_in = existing_time_in or now
            elif item.status == "excused":
                assessment = "valid_presence"
                time_in = existing_time_in
            else:
                assessment = "absent"
                time_in = existing_time_in

            lock_status = payload.lock_status or item.status in {"present", "late", "excused"}
            self.repo.apply_manual_status(
                record_id=item.record_id,
                professor_id=payload.professor_id,
                previous_status=previous_status,
                new_status=item.status,
                system_assessment=assessment,
                time_in=time_in,
                notes=payload.notes,
                lock_status=lock_status,
            )
            if item.status in {"present", "late"} and not existing_time_in:
                self.repo.create_event(
                    session_id=session_id,
                    record_id=item.record_id,
                    student_id=item.student_id,
                    event_type="manual_attendance",
                    event_time=now,
                    event_source="manual_professor",
                    recognition_confidence=None,
                    notes=payload.notes or f"Marked {item.status} from manual attendance.",
                )

        return self.get_session_detail(session_id)

    def start_break(self, session_id: int) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "on_break":
            return self.get_session_detail(session_id)
        if session.session_status != "in_progress":
            raise HTTPException(status_code=400, detail="Session break can only start during an in-progress session.")

        now = datetime.now(MANILA_TZ).replace(tzinfo=None)
        self.repo.set_session_status(session_id, "on_break")
        session = self._get_session_or_404(session_id)

        for record_id, student_id, _final_status, _time_in in self.repo.list_break_candidate_records(session_id):
            last_event = self.repo.get_student_events(session_id, int(student_id))[-1:]
            if last_event and last_event[0][0] == "break_out":
                continue

            self.repo.create_event(
                session_id=session_id,
                record_id=int(record_id),
                student_id=int(student_id),
                event_type="break_out",
                event_time=now,
                event_source="system",
                recognition_confidence=None,
                notes="Session Break started by professor. Return Detection Mode enabled.",
            )
            self._recalculate_student_record(session, int(record_id), int(student_id))

        return self.get_session_detail(session_id)

    def end_break(self, session_id: int, payload: V2BreakUnlockRequest) -> V2SessionDetailResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status != "on_break":
            raise HTTPException(status_code=400, detail="Session is not currently on break.")
        if not verify_user_password(payload.professor_email, payload.password):
            raise HTTPException(status_code=401, detail="Professor password verification failed.")

        self.repo.set_session_status(session_id, "in_progress")
        return self.get_session_detail(session_id)

    def end_session(self, session_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "finalized":
            return self.get_session_review(session_id)
        if session.session_status == "on_break":
            raise HTTPException(status_code=423, detail="Session Break is active. End break before ending the session.")
        if session.session_status not in {"in_progress", "under_review"}:
            raise HTTPException(status_code=400, detail="Session cannot be ended from its current status.")

        self.repo.end_session(session_id, datetime.now(MANILA_TZ).replace(tzinfo=None))
        refreshed = self._get_session_or_404(session_id)
        for record in self._get_roster(session_id):
            self._recalculate_student_record(refreshed, record.record_id, record.student_id)
        return self.get_session_review(session_id)

    def finalize_session(self, session_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "finalized":
            return self.get_session_review(session_id)
        if session.session_status == "on_break":
            raise HTTPException(status_code=423, detail="Session Break is active. End break before finalizing attendance.")
        if session.session_status not in {"under_review", "in_progress"}:
            raise HTTPException(status_code=400, detail="Session cannot be finalized from its current status.")

        for record in self._get_roster(session_id):
            self._recalculate_student_record(session, record.record_id, record.student_id)
        self.repo.confirm_session_records(session_id)
        self.repo.finalize_session(session_id, datetime.now(MANILA_TZ).replace(tzinfo=None))
        return self.get_session_review(session_id)

    def confirm_student_record(self, session_id: int, student_id: int) -> V2SessionReviewResponse:
        session = self._get_session_or_404(session_id)
        if session.session_status == "finalized":
            raise HTTPException(status_code=400, detail="Finalized sessions cannot be changed.")
        if session.session_status == "on_break":
            raise HTTPException(status_code=423, detail="Session Break is active. Student confirmations are locked until the professor ends break.")
        if session.session_status not in {"under_review", "in_progress"}:
            raise HTTPException(status_code=400, detail="Session is not accepting confirmations.")

        record_row = self.repo.get_record_for_student(session_id, student_id)
        if not record_row:
            raise HTTPException(status_code=404, detail="Student is not enrolled in this session.")

        self.repo.confirm_student_record(session_id, student_id)
        return self.get_session_review(session_id)

    def _recalculate_student_record(self, session: V2SessionResponse, record_id: int, student_id: int) -> None:
        record_state = self.repo.get_record_recalculation_state(record_id)
        professor_confirmed = bool(record_state[2]) if record_state else False
        professor_status = str(record_state[0]) if record_state else ""
        events = self.repo.get_student_events(session.session_id, student_id)
        normalized = [(row[0], self._coerce_datetime(row[1])) for row in events]
        time_in = next((event_time for event_type, event_time in normalized if event_type in {"time_in", "manual_attendance"}), None)
        time_out = None
        presence_minutes = 0
        outside_minutes = 0
        break_count = 0
        outside_started_at = None
        inside_started_at = None

        session_start = session.actual_start or session.scheduled_start
        session_end = session.actual_end or datetime.now(MANILA_TZ).replace(tzinfo=None)

        for event_type, event_time in normalized:
            if event_type in {"time_in", "break_in", "manual_attendance"}:
                if outside_started_at:
                    outside_minutes += self._minutes_between(outside_started_at, event_time)
                    outside_started_at = None
                if not inside_started_at:
                    inside_started_at = event_time
                if not time_in:
                    time_in = event_time
            elif event_type in {"break_out", "time_out"}:
                if inside_started_at:
                    presence_minutes += self._minutes_between(inside_started_at, event_time)
                    inside_started_at = None
                if event_type == "break_out":
                    break_count += 1
                    outside_started_at = event_time
                else:
                    time_out = event_time

        if inside_started_at:
            presence_minutes += self._minutes_between(inside_started_at, session_end)
        if outside_started_at:
            outside_minutes += self._minutes_between(outside_started_at, session_end)

        monitored_minutes = max(1, self._minutes_between(session_start, session_end))
        ratio = presence_minutes / monitored_minutes
        late_minutes = 0
        if time_in:
            late_minutes = max(0, self._minutes_between(session_start, time_in))

        if not time_in:
            final_status = "absent"
            system_assessment = "absent"
            requires_review = False
            review_reason = None
        elif late_minutes > 30:
            final_status = "absent"
            system_assessment = "requires_review"
            requires_review = True
            review_reason = (
                f"Student arrived {late_minutes} minutes after the monitored session started. "
                "Marked absent by attendance policy; professor may override to Late or Present."
            )
        elif late_minutes > 15:
            final_status = "late"
            system_assessment = self._assessment_from_ratio(ratio)
            requires_review = system_assessment == "requires_review"
            review_reason = (
                f"Student arrived {late_minutes} minutes after the monitored session started."
                if system_assessment == "valid_presence"
                else self._presence_review_reason(presence_minutes, monitored_minutes)
            )
        elif ratio >= 0.8:
            final_status = "present"
            system_assessment = "valid_presence"
            requires_review = False
            review_reason = None
        elif ratio >= 0.6:
            final_status = "present"
            system_assessment = "attendance_warning"
            requires_review = False
            review_reason = self._presence_review_reason(presence_minutes, monitored_minutes)
        else:
            final_status = "present"
            system_assessment = "requires_review"
            requires_review = True
            review_reason = self._presence_review_reason(presence_minutes, monitored_minutes)

        if professor_confirmed and professor_status in {"present", "late", "absent", "excused"}:
            final_status = professor_status
            if final_status in {"present", "late", "excused"}:
                system_assessment = "valid_presence"
            else:
                system_assessment = "absent"
            requires_review = False
            review_reason = None

        self.repo.update_student_record(
            record_id=record_id,
            final_status=final_status,
            system_assessment=system_assessment,
            time_in=time_in,
            time_out=time_out,
            total_presence_minutes=presence_minutes,
            total_outside_minutes=outside_minutes,
            break_count=break_count,
            late_minutes=late_minutes,
            requires_review=requires_review,
            review_reason=review_reason,
        )

    def _v2_similarity_threshold(self, configured_distance_threshold: float) -> float:
        configured_similarity = similarity_threshold_from_distance_threshold(configured_distance_threshold)
        return max(configured_similarity, V2_MIN_RECOGNITION_SIMILARITY)

    def _confidence_percent(self, similarity: float) -> float:
        return round(min(100.0, max(0.0, similarity * 100)), 2)

    def _decide_recognition_match(
        self,
        candidates: list[dict],
        threshold: float,
        margin: float,
    ) -> dict:
        best = candidates[0] if candidates else None
        second = candidates[1] if len(candidates) > 1 else None
        if not best:
            return {"result": "no_enrolled_profiles", "best": None, "second": None}

        best_score = float(best["similarity"])
        second_score = float(second["similarity"]) if second else -1.0
        if best_score < threshold:
            return {"result": "below_threshold", "best": best, "second": second}
        if second and best_score - second_score < margin:
            return {"result": "ambiguous_match", "best": best, "second": second}
        return {"result": "recognized", "best": best, "second": second}

    def _get_session_or_404(self, session_id: int) -> V2SessionResponse:
        row = self.repo.get_session(session_id)
        if not row:
            raise HTTPException(status_code=404, detail="Session not found.")
        return V2SessionResponse(
            session_id=row[0],
            class_id=row[1],
            professor_id=row[2],
            scheduled_start=self._coerce_datetime(row[3]),
            scheduled_end=self._coerce_datetime(row[4]),
            actual_start=self._coerce_datetime(row[5]) if row[5] else None,
            actual_end=self._coerce_datetime(row[6]) if row[6] else None,
            session_status=row[7],
            student_record_count=row[8],
        )

    def _get_roster(self, session_id: int) -> list[V2StudentRecord]:
        records = []
        for row in self.repo.list_session_records(session_id):
            records.append(
                V2StudentRecord(
                    record_id=row[0],
                    student_id=row[1],
                    student_number=row[2],
                    student_name=f"{row[4]}, {row[3]}",
                    final_status=row[5],
                    system_assessment=row[6],
                    time_in=self._coerce_datetime(row[7]) if row[7] else None,
                    time_out=self._coerce_datetime(row[8]) if row[8] else None,
                    total_presence_minutes=row[9],
                    total_outside_minutes=row[10],
                    break_count=row[11],
                    late_minutes=row[12],
                    requires_review=bool(row[13]),
                    review_reason=row[14],
                    confirmed_by_professor=bool(row[15]),
                    confirmed_at=self._coerce_datetime(row[16]) if row[16] else None,
                )
            )
        return records

    def _get_events(self, session_id: int) -> list[V2AttendanceEvent]:
        events = []
        for row in self.repo.list_session_events(session_id):
            events.append(
                V2AttendanceEvent(
                    event_id=row[0],
                    session_id=row[1],
                    record_id=row[2],
                    student_id=row[3],
                    event_type=row[4],
                    event_time=self._coerce_datetime(row[5]),
                    event_source=row[6],
                    recognition_confidence=float(row[7]) if row[7] is not None else None,
                    notes=row[8],
                    is_voided=bool(row[9]),
                )
            )
        return events

    def _build_review_summary(self, roster: list[V2StudentRecord]) -> V2ReviewSummary:
        total = len(roster)
        present = sum(1 for record in roster if record.final_status == "present")
        late = sum(1 for record in roster if record.final_status == "late")
        partial = sum(1 for record in roster if record.system_assessment in {"attendance_warning", "requires_review"})
        absent = sum(1 for record in roster if record.final_status == "absent")
        excused = sum(1 for record in roster if record.final_status == "excused")
        review = sum(1 for record in roster if record.requires_review)
        validated = present + late + excused
        rate = round((validated / total) * 100, 2) if total else 0.0
        return V2ReviewSummary(
            present_count=present,
            late_count=late,
            partial_count=partial,
            absent_count=absent,
            excused_count=excused,
            students_requiring_review=review,
            total_students=total,
            presence_validation_rate=rate,
        )

    def _class_status(
        self,
        target_date: date,
        start_time: time,
        end_time: time,
        now: datetime,
    ) -> str:
        start_dt = self._combine_local(target_date, start_time)
        end_dt = self._combine_local(target_date, end_time)
        local_now = now.replace(tzinfo=None)
        if start_dt <= local_now <= end_dt:
            return "current"
        if local_now < start_dt:
            return "upcoming"
        return "completed"

    def _history_status(self, session_status: str, warning_count: int) -> str:
        if session_status in {"in_progress", "on_break"}:
            return "in_progress"
        if session_status == "under_review" or warning_count > 0:
            return "needs_review"
        return "completed"

    def _get_class_student_history(self, class_id: int, student_id: int) -> list[V2ClassRosterHistoryItem]:
        history = []
        for row in self.repo.list_class_roster_student_history(class_id, student_id):
            status = str(row[2])
            note = "Requires professor review" if row[4] else str(row[3]).replace("_", " ").title()
            history.append(
                V2ClassRosterHistoryItem(
                    session_id=row[0],
                    session_date=self._coerce_datetime(row[1]).date(),
                    status=status,
                    note=note,
                )
            )
        return history

    def _face_profile_status(self, profile_count: int, last_face_update: datetime | None) -> str:
        if profile_count <= 0:
            return "no_face_profile"
        if last_face_update and (datetime.now(MANILA_TZ).replace(tzinfo=None) - last_face_update).days > 180:
            return "needs_update"
        return "registered"

    def _recognition_status(
        self,
        profile_count: int,
        recognition_confidence: float | None,
        last_recognition_at: datetime | None,
    ) -> str:
        if profile_count <= 0:
            return "not_available"
        if recognition_confidence is not None and recognition_confidence < 80:
            return "low_confidence"
        if not last_recognition_at:
            return "not_recognized_recently"
        if (datetime.now(MANILA_TZ).replace(tzinfo=None) - last_recognition_at).days > 30:
            return "not_recognized_recently"
        return "active"

    def _assessment_from_ratio(self, ratio: float) -> str:
        if ratio >= 0.8:
            return "valid_presence"
        if ratio >= 0.6:
            return "attendance_warning"
        return "requires_review"

    def _presence_review_reason(self, presence_minutes: int, monitored_minutes: int) -> str:
        return (
            f"Student had {presence_minutes} minutes of monitored presence out of "
            f"{monitored_minutes} minutes. Professor review is recommended."
        )

    def _combine_local(self, value_date: date, value_time: time) -> datetime:
        return datetime.combine(value_date, value_time)

    def _coerce_time(self, value) -> time:
        if isinstance(value, time):
            return value
        text = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Invalid time value: {value}")

    def _coerce_datetime(self, value) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        text = str(value).strip().replace("T", " ")
        if text.endswith("Z"):
            text = text[:-1]
        if "+" in text[10:]:
            text = text.split("+", 1)[0]
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return datetime.fromisoformat(text).replace(tzinfo=None)

    def _minutes_between(self, start: datetime, end: datetime) -> int:
        return max(0, int((end - start).total_seconds() // 60))


def get_v2_attendance_service() -> V2AttendanceService:
    return V2AttendanceService()
