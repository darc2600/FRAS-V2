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
                    r.review_reason
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
                  AND final_status IN ('present', 'late', 'partial')
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
    ) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE student_session_records
                SET final_status = ?,
                    system_assessment = ?,
                    time_in = COALESCE(?, time_in),
                    requires_review = FALSE,
                    review_reason = NULL,
                    confirmed_by_professor = TRUE,
                    confirmed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE record_id = ?
                """,
                (new_status, system_assessment, time_in, record_id),
            )
            cursor.execute(
                """
                INSERT INTO professor_overrides (
                    record_id, professor_id, override_type,
                    previous_status, new_status, reason, notes
                )
                VALUES (?, ?, 'manual_attendance', ?, ?, 'Manual attendance modal', ?)
                """,
                (record_id, professor_id, previous_status, new_status, notes),
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
                  AND session_status IN ('in_progress', 'on_break')
                """,
                (actual_end, session_id),
            )
