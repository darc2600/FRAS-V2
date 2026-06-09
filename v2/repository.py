from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from services.db import get_connection


class V2AttendanceRepository:
    def list_professors(self) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    professor_id,
                    user_id,
                    faculty_number,
                    first_name,
                    last_name,
                    email,
                    COALESCE(total_units, 0),
                    COALESCE(lecture_units, 0),
                    COALESCE(lab_units, 0)
                FROM professors
                ORDER BY last_name, first_name, professor_id
                """
            )
            return cursor.fetchall()

    def list_professor_classes_for_day(self, professor_id: int, day_of_week: str) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    c.day_of_week,
                    c.start_time,
                    c.end_time,
                    COUNT(e.student_id) AS student_count,
                    (
                        SELECT s.session_id
                        FROM attendance_sessions s
                        WHERE s.class_id = c.class_id
                          AND s.professor_id = c.professor_id
                          AND s.session_status IN ('in_progress', 'on_break', 'under_review')
                        ORDER BY s.created_at DESC
                        LIMIT 1
                    ) AS active_session_id
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                LEFT JOIN enrollments e ON e.class_id = c.class_id
                    AND e.enrollment_status = 'active'
                WHERE c.professor_id = ?
                  AND c.day_of_week = ?
                  AND c.is_active = TRUE
                GROUP BY
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    c.day_of_week,
                    c.start_time,
                    c.end_time
                ORDER BY c.start_time, co.course_code, c.section
                """,
                (professor_id, day_of_week),
            )
            return cursor.fetchall()

    def list_professor_schedule(self, professor_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    c.day_of_week,
                    c.start_time,
                    c.end_time,
                    COUNT(e.student_id) AS student_count
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                LEFT JOIN enrollments e ON e.class_id = c.class_id
                    AND e.enrollment_status = 'active'
                WHERE c.professor_id = ?
                  AND c.is_active = TRUE
                GROUP BY
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    c.day_of_week,
                    c.start_time,
                    c.end_time
                ORDER BY
                    CASE c.day_of_week
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                        ELSE 8
                    END,
                    c.start_time,
                    co.course_code,
                    c.section
                """,
                (professor_id,),
            )
            return cursor.fetchall()

    def get_class_history_context(self, class_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    p.last_name,
                    p.first_name
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                JOIN professors p ON p.professor_id = c.professor_id
                WHERE c.class_id = ?
                """,
                (class_id,),
            )
            return cursor.fetchone()

    def list_class_session_history(self, class_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.session_status,
                    COUNT(r.record_id) AS total_students,
                    COALESCE(SUM(CASE
                        WHEN r.final_status IN ('present', 'late', 'excused') THEN 1
                        ELSE 0
                    END), 0) AS attendance_count,
                    COALESCE(AVG(r.total_presence_minutes), 0) AS average_presence_minutes,
                    COALESCE(SUM(CASE
                        WHEN r.requires_review = TRUE THEN 1
                        ELSE 0
                    END), 0) AS warning_count,
                    COALESCE(SUM(CASE
                        WHEN r.final_status = 'excused' THEN 1
                        ELSE 0
                    END), 0) AS excused_count
                FROM attendance_sessions s
                LEFT JOIN student_session_records r ON r.session_id = s.session_id
                WHERE s.class_id = ?
                GROUP BY
                    s.session_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.session_status
                ORDER BY s.scheduled_start DESC, s.session_id DESC
                """,
                (class_id,),
            )
            return cursor.fetchall()

    def get_professor_history_context(self, professor_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT professor_id, first_name, last_name
                FROM professors
                WHERE professor_id = ?
                """,
                (professor_id,),
            )
            return cursor.fetchone()

    def list_professor_session_history(self, professor_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.session_status,
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    COUNT(ss.record_id) AS total_students,
                    COALESCE(SUM(CASE
                        WHEN ss.final_status IN ('present', 'late', 'excused') THEN 1
                        ELSE 0
                    END), 0) AS attendance_count,
                    COALESCE(AVG(ss.total_presence_minutes), 0) AS average_presence_minutes,
                    COALESCE(SUM(CASE
                        WHEN ss.requires_review = TRUE THEN 1
                        ELSE 0
                    END), 0) AS warning_count,
                    COALESCE(SUM(CASE
                        WHEN ss.final_status = 'excused' THEN 1
                        ELSE 0
                    END), 0) AS excused_count
                FROM attendance_sessions s
                JOIN classes c ON c.class_id = s.class_id
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                LEFT JOIN student_session_records ss ON ss.session_id = s.session_id
                WHERE c.professor_id = ?
                GROUP BY
                    s.session_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.session_status,
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number
                ORDER BY s.scheduled_start DESC, s.session_id DESC
                """,
                (professor_id,),
            )
            return cursor.fetchall()

    def get_class_roster_context(self, class_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    p.last_name,
                    p.first_name,
                    COUNT(e.student_id) AS student_count
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                JOIN professors p ON p.professor_id = c.professor_id
                LEFT JOIN enrollments e ON e.class_id = c.class_id
                    AND e.enrollment_status = 'active'
                WHERE c.class_id = ?
                GROUP BY
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    p.last_name,
                    p.first_name
                """,
                (class_id,),
            )
            return cursor.fetchone()

    def list_class_roster_students(self, class_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.student_id,
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    s.email,
                    MAX(COALESCE(fp.updated_at, fp.registered_at)) AS last_face_update,
                    COUNT(DISTINCT fp.face_profile_id) AS face_profile_count,
                    COUNT(DISTINCT ss.record_id) AS total_sessions,
                    COALESCE(SUM(CASE WHEN ss.final_status = 'present' THEN 1 ELSE 0 END), 0) AS present_sessions,
                    COALESCE(SUM(CASE WHEN ss.final_status = 'late' THEN 1 ELSE 0 END), 0) AS late_sessions,
                    COALESCE(SUM(CASE WHEN ss.final_status = 'partial' THEN 1 ELSE 0 END), 0) AS partial_sessions,
                    COALESCE(SUM(CASE WHEN ss.final_status = 'absent' THEN 1 ELSE 0 END), 0) AS absent_sessions,
                    COALESCE(SUM(CASE WHEN ss.final_status = 'excused' THEN 1 ELSE 0 END), 0) AS excused_sessions,
                    MAX(ae.recognition_confidence) AS recognition_confidence,
                    MAX(ae.event_time) AS last_recognition_at
                FROM enrollments e
                JOIN students s ON s.student_id = e.student_id
                LEFT JOIN student_face_profiles fp ON fp.student_id = s.student_id
                    AND fp.is_active = TRUE
                LEFT JOIN attendance_sessions sess ON sess.class_id = e.class_id
                LEFT JOIN student_session_records ss ON ss.session_id = sess.session_id
                    AND ss.student_id = s.student_id
                LEFT JOIN attendance_events ae ON ae.session_id = sess.session_id
                    AND ae.student_id = s.student_id
                    AND ae.recognition_confidence IS NOT NULL
                    AND ae.is_voided = FALSE
                WHERE e.class_id = ?
                  AND e.enrollment_status = 'active'
                GROUP BY
                    s.student_id,
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    s.email
                ORDER BY s.last_name, s.first_name, s.student_number
                """,
                (class_id,),
            )
            return cursor.fetchall()

    def list_class_roster_student_history(self, class_id: int, student_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    sess.session_id,
                    sess.scheduled_start,
                    ss.final_status,
                    ss.system_assessment,
                    ss.requires_review
                FROM attendance_sessions sess
                JOIN student_session_records ss ON ss.session_id = sess.session_id
                WHERE sess.class_id = ?
                  AND ss.student_id = ?
                ORDER BY sess.scheduled_start DESC, sess.session_id DESC
                """,
                (class_id, student_id),
            )
            return cursor.fetchall()

    def get_student_class_history_header(self, class_id: int, student_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    st.student_id,
                    st.student_number,
                    st.first_name,
                    st.last_name,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                JOIN enrollments e ON e.class_id = c.class_id
                    AND e.enrollment_status = 'active'
                JOIN students st ON st.student_id = e.student_id
                WHERE c.class_id = ?
                  AND st.student_id = ?
                """,
                (class_id, student_id),
            )
            return cursor.fetchone()

    def list_student_class_history_records(self, class_id: int, student_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    sess.session_id,
                    sess.scheduled_start,
                    sess.scheduled_end,
                    ss.final_status,
                    ss.total_presence_minutes,
                    ss.total_outside_minutes,
                    ss.break_count,
                    ss.system_assessment
                FROM attendance_sessions sess
                JOIN student_session_records ss ON ss.session_id = sess.session_id
                WHERE sess.class_id = ?
                  AND ss.student_id = ?
                ORDER BY sess.scheduled_start DESC, sess.session_id DESC
                """,
                (class_id, student_id),
            )
            return cursor.fetchall()

    def get_face_profile_context(self, class_id: int, student_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.class_id,
                    st.student_id,
                    st.student_number,
                    st.first_name,
                    st.last_name,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number,
                    MAX(COALESCE(fp.updated_at, fp.registered_at)) AS last_face_update,
                    COUNT(DISTINCT fp.face_profile_id) AS face_profile_count
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                LEFT JOIN rooms r ON r.room_id = c.room_id
                JOIN enrollments e ON e.class_id = c.class_id
                    AND e.enrollment_status = 'active'
                JOIN students st ON st.student_id = e.student_id
                LEFT JOIN student_face_profiles fp ON fp.student_id = st.student_id
                    AND fp.is_active = TRUE
                WHERE c.class_id = ?
                  AND st.student_id = ?
                GROUP BY
                    c.class_id,
                    st.student_id,
                    st.student_number,
                    st.first_name,
                    st.last_name,
                    co.course_code,
                    co.course_name,
                    c.section,
                    r.room_number
                """,
                (class_id, student_id),
            )
            return cursor.fetchone()

    def get_student_name_for_class(self, class_id: int, student_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT st.first_name, st.last_name
                FROM enrollments e
                JOIN students st ON st.student_id = e.student_id
                WHERE e.class_id = ?
                  AND e.student_id = ?
                  AND e.enrollment_status = 'active'
                """,
                (class_id, student_id),
            )
            return cursor.fetchone()

    def replace_student_face_profile(
        self,
        student_id: int,
        face_image_path: str | None,
        embedding_json: str | None,
        model_name: str | None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE student_face_profiles
                SET is_active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = ?
                  AND is_active = TRUE
                """,
                (student_id,),
            )
            cursor.execute(
                """
                INSERT INTO student_face_profiles (
                    student_id,
                    face_image_path,
                    embedding_json,
                    model_name,
                    is_active,
                    registered_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING face_profile_id
                """,
                (student_id, face_image_path, embedding_json, model_name),
            )
            return int(cursor.fetchone()[0])

    def get_class_for_session_start(self, class_id: int, professor_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT class_id, professor_id, day_of_week, start_time, end_time
                FROM classes
                WHERE class_id = ?
                  AND professor_id = ?
                  AND is_active = TRUE
                """,
                (class_id, professor_id),
            )
            return cursor.fetchone()

    def get_active_session(self, class_id: int, professor_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.class_id,
                    s.professor_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.actual_start,
                    s.actual_end,
                    s.session_status,
                    COUNT(r.record_id) AS student_record_count
                FROM attendance_sessions s
                LEFT JOIN student_session_records r ON r.session_id = s.session_id
                WHERE s.class_id = ?
                  AND s.professor_id = ?
                  AND s.session_status IN ('in_progress', 'on_break', 'under_review')
                GROUP BY s.session_id
                ORDER BY s.created_at DESC
                LIMIT 1
                """,
                (class_id, professor_id),
            )
            return cursor.fetchone()

    def create_session(
        self,
        class_id: int,
        professor_id: int,
        scheduled_start: datetime,
        scheduled_end: datetime,
        actual_start: datetime,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO attendance_sessions (
                    class_id, professor_id, scheduled_start, scheduled_end,
                    actual_start, session_status
                )
                VALUES (?, ?, ?, ?, ?, 'in_progress')
                RETURNING session_id
                """,
                (class_id, professor_id, scheduled_start, scheduled_end, actual_start),
            )
            session_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO student_session_records (session_id, student_id)
                SELECT ?, e.student_id
                FROM enrollments e
                WHERE e.class_id = ?
                  AND e.enrollment_status = 'active'
                ON CONFLICT (session_id, student_id) DO NOTHING
                """,
                (session_id, class_id),
            )
            return int(session_id)

    def get_session(self, session_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.class_id,
                    s.professor_id,
                    s.scheduled_start,
                    s.scheduled_end,
                    s.actual_start,
                    s.actual_end,
                    s.session_status,
                    COUNT(r.record_id) AS student_record_count
                FROM attendance_sessions s
                LEFT JOIN student_session_records r ON r.session_id = s.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id
                """,
                (session_id,),
            )
            return cursor.fetchone()

    def list_session_records(self, session_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    r.record_id,
                    s.student_id,
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    r.final_status,
                    r.system_assessment,
                    r.time_in,
                    r.time_out,
                    r.total_presence_minutes,
                    r.total_outside_minutes,
                    r.break_count,
                    r.late_minutes,
                    r.requires_review,
                    r.review_reason,
                    r.confirmed_by_professor,
                    r.confirmed_at
                FROM student_session_records r
                JOIN students s ON s.student_id = r.student_id
                WHERE r.session_id = ?
                ORDER BY s.last_name, s.first_name, s.student_number
                """,
                (session_id,),
            )
            return cursor.fetchall()

    def list_session_events(self, session_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    event_id,
                    session_id,
                    record_id,
                    student_id,
                    event_type,
                    event_time,
                    event_source,
                    recognition_confidence,
                    notes,
                    is_voided
                FROM attendance_events
                WHERE session_id = ?
                ORDER BY event_time, event_id
                """,
                (session_id,),
            )
            return cursor.fetchall()

    def get_record_for_student(self, session_id: int, student_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT record_id
                FROM student_session_records
                WHERE session_id = ?
                  AND student_id = ?
                """,
                (session_id, student_id),
            )
            return cursor.fetchone()

    def get_record_for_override(self, session_id: int, record_id: int, student_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    record_id,
                    final_status,
                    time_in
                FROM student_session_records
                WHERE session_id = ?
                  AND record_id = ?
                  AND student_id = ?
                """,
                (session_id, record_id, student_id),
            )
            return cursor.fetchone()

    def list_break_candidate_records(self, session_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    record_id,
                    student_id,
                    final_status,
                    time_in
                FROM student_session_records
                WHERE session_id = ?
                  AND final_status IN ('present', 'late')
                  AND time_in IS NOT NULL
                ORDER BY record_id
                """,
                (session_id,),
            )
            return cursor.fetchall()

    def create_event(
        self,
        session_id: int,
        record_id: int,
        student_id: int,
        event_type: str,
        event_time: datetime,
        event_source: str,
        recognition_confidence: Optional[float],
        notes: Optional[str],
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO attendance_events (
                    session_id, record_id, student_id, event_type, event_time,
                    event_source, recognition_confidence, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING event_id
                """,
                (
                    session_id,
                    record_id,
                    student_id,
                    event_type,
                    event_time,
                    event_source,
                    recognition_confidence,
                    notes,
                ),
            )
            return int(cursor.fetchone()[0])

    def get_student_events(self, session_id: int, student_id: int) -> list[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT event_type, event_time
                FROM attendance_events
                WHERE session_id = ?
                  AND student_id = ?
                  AND is_voided = FALSE
                ORDER BY event_time, event_id
                """,
                (session_id, student_id),
            )
            return cursor.fetchall()

    def get_record_recalculation_state(self, record_id: int) -> Optional[tuple[Any, ...]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    final_status,
                    system_assessment,
                    confirmed_by_professor
                FROM student_session_records
                WHERE record_id = ?
                """,
                (record_id,),
            )
            return cursor.fetchone()

    def update_student_record(
        self,
        record_id: int,
        final_status: str,
        system_assessment: str,
        time_in: Optional[datetime],
        time_out: Optional[datetime],
        total_presence_minutes: int,
        total_outside_minutes: int,
        break_count: int,
        late_minutes: int,
        requires_review: bool,
        review_reason: Optional[str],
    ) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE student_session_records
                SET final_status = ?,
                    system_assessment = ?,
                    time_in = ?,
                    time_out = ?,
                    total_presence_minutes = ?,
                    total_outside_minutes = ?,
                    break_count = ?,
                    late_minutes = ?,
                    requires_review = ?,
                    review_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE record_id = ?
                """,
                (
                    final_status,
                    system_assessment,
                    time_in,
                    time_out,
                    total_presence_minutes,
                    total_outside_minutes,
                    break_count,
                    late_minutes,
                    requires_review,
                    review_reason,
                    record_id,
                ),
            )

    def apply_manual_status(
        self,
        record_id: int,
        professor_id: int,
        previous_status: str,
        new_status: str,
        system_assessment: str,
        time_in: Optional[datetime],
        notes: Optional[str],
        lock_status: bool,
    ) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            confirmed_at_sql = "CURRENT_TIMESTAMP" if lock_status else "NULL"
            cursor.execute(
                f"""
                UPDATE student_session_records
                SET final_status = ?,
                    system_assessment = ?,
                    time_in = COALESCE(?, time_in),
                    requires_review = FALSE,
                    review_reason = NULL,
                    confirmed_by_professor = ?,
                    confirmed_at = {confirmed_at_sql},
                    updated_at = CURRENT_TIMESTAMP
                WHERE record_id = ?
                """,
                (new_status, system_assessment, time_in, lock_status, record_id),
            )
            cursor.execute(
                """
                INSERT INTO professor_overrides (
                    record_id, professor_id, override_type,
                    previous_status, new_status, reason, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    professor_id,
                    "final_override" if lock_status else "manual_attendance",
                    previous_status,
                    new_status,
                    "Professor final override" if lock_status else "Live manual attendance input",
                    notes,
                ),
            )

    def confirm_student_record(self, session_id: int, student_id: int) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE student_session_records
                SET confirmed_by_professor = TRUE,
                    confirmed_at = CURRENT_TIMESTAMP,
                    requires_review = FALSE,
                    review_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND student_id = ?
                """,
                (session_id, student_id),
            )

    def confirm_session_records(self, session_id: int) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE student_session_records
                SET confirmed_by_professor = TRUE,
                    confirmed_at = CURRENT_TIMESTAMP,
                    requires_review = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )

    def set_session_status(self, session_id: int, status: str) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE attendance_sessions
                SET session_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (status, session_id),
            )

    def end_session(self, session_id: int, actual_end: datetime) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE attendance_sessions
                SET actual_end = ?,
                    session_status = 'under_review',
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND session_status IN ('in_progress')
                """,
                (actual_end, session_id),
            )

    def finalize_session(self, session_id: int, finalized_at: datetime) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE attendance_sessions
                SET finalized_at = ?,
                    session_status = 'finalized',
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND session_status IN ('under_review', 'in_progress')
                """,
                (finalized_at, session_id),
            )
