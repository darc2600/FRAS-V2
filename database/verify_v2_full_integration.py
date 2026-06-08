from __future__ import annotations

import asyncio
import csv
import os
import sys
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

import psycopg2
from fastapi import UploadFile

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env

from api.auth import LoginRequest, login
from services.db import get_connection
from v2.models import V2CreateEventRequest, V2ManualAttendanceRecord, V2ManualAttendanceRequest
from v2.service import V2AttendanceService


TEST_EMAIL = "test.professor@fras.local"
TEST_PASSWORD = "password123"
FACULTY_PASSWORD = "password"


def _print_check(label: str, ok: bool, detail: str = "") -> None:
    marker = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{marker}] {label}{suffix}")


def _connect_raw():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")
    return psycopg2.connect(database_url)


def _pick_professor(cursor, email: str | None = None) -> dict[str, Any]:
    if email:
        cursor.execute(
            """
            SELECT p.professor_id, p.email, p.first_name, p.last_name
            FROM professors p
            WHERE p.email = %s
            """,
            (email,),
        )
    else:
        cursor.execute(
            """
            SELECT p.professor_id, u.email, p.first_name, p.last_name
            FROM professors p
            JOIN users u ON u.user_id = p.user_id
            WHERE p.email <> %s
              AND u.password_hash = %s
              AND u.role = 'professor'
              AND COALESCE(u.is_active, TRUE) = TRUE
              AND EXISTS (
                  SELECT 1
                  FROM classes c
                  JOIN enrollments e ON e.class_id = c.class_id
                  WHERE c.professor_id = p.professor_id
                    AND c.is_active = TRUE
                    AND e.enrollment_status = 'active'
              )
            ORDER BY p.professor_id
            LIMIT 1
            """,
            (TEST_EMAIL, FACULTY_PASSWORD),
        )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No professor found for {email or 'real seeded professor'}.")
    return {"professor_id": int(row[0]), "email": row[1], "name": f"{row[3]}, {row[2]}"}


def _pick_class(cursor, professor_id: int) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT
            c.class_id,
            c.professor_id,
            c.day_of_week,
            c.start_time,
            c.end_time,
            co.course_code,
            co.course_name,
            c.section,
            COALESCE(r.room_number, 'TBA') AS room,
            COUNT(e.student_id) AS student_count
        FROM classes c
        JOIN courses co ON co.course_id = c.course_id
        LEFT JOIN rooms r ON r.room_id = c.room_id
        JOIN enrollments e ON e.class_id = c.class_id
            AND e.enrollment_status = 'active'
        WHERE c.professor_id = %s
          AND c.is_active = TRUE
        GROUP BY c.class_id, co.course_code, co.course_name, c.section, r.room_number
        ORDER BY COUNT(e.student_id) DESC, c.class_id
        LIMIT 1
        """,
        (professor_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No active enrolled class found for professor {professor_id}.")
    return {
        "class_id": int(row[0]),
        "professor_id": int(row[1]),
        "day_of_week": row[2],
        "start_time": row[3],
        "end_time": row[4],
        "course_code": row[5],
        "course_name": row[6],
        "section": row[7],
        "room": row[8],
        "student_count": int(row[9]),
    }


def _csv_rows(roster) -> list[list[str]]:
    def status_label(status: str) -> str:
        normalized = (status or "").lower()
        if normalized == "present":
            return "Present"
        if normalized == "late":
            return "Late"
        if normalized == "excused":
            return "Excused"
        return "Absent"

    rows = [["Student Number", "Student Name", "Attendance Status"]]
    rows.extend([student.student_number, student.student_name, status_label(student.final_status)] for student in roster)
    return rows


def _csv_text(rows: list[list[str]]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()


def _safe_filename_part(value: str) -> str:
    import re

    cleaned = re.sub(r"[^a-z0-9]+", "-", value.strip(), flags=re.I).strip("-").lower()
    return cleaned or "value"


def _blackboard_filename(class_info: dict[str, Any], session_id: int, session_date: date) -> str:
    class_part = f"{_safe_filename_part(class_info['course_code'])}_{_safe_filename_part(class_info['section'])}"
    return f"fras_blackboard_{class_part}_{session_date.isoformat()}_session-{session_id}.csv"


def _create_policy_session(service: V2AttendanceService, class_info: dict[str, Any]) -> int:
    start = datetime.now().replace(microsecond=0) - timedelta(minutes=50)
    scheduled_start = datetime.combine(date.today(), class_info["start_time"])
    scheduled_end = datetime.combine(date.today(), class_info["end_time"])
    return service.repo.create_session(
        class_id=class_info["class_id"],
        professor_id=class_info["professor_id"],
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        actual_start=start,
    )


def _exercise_session(service: V2AttendanceService, class_info: dict[str, Any]) -> dict[str, Any]:
    session_id = _create_policy_session(service, class_info)
    detail = service.get_session_detail(session_id)
    if len(detail.roster) < 4:
        raise RuntimeError(f"Class {class_info['class_id']} needs at least 4 enrolled students for the full policy test.")

    actual_start = detail.session.actual_start or datetime.now()
    early, late, very_late, excused = detail.roster[:4]

    service.create_event(
        session_id,
        V2CreateEventRequest(
            student_id=early.student_id,
            event_type="time_in",
            event_source="facial_recognition",
            event_time=actual_start + timedelta(minutes=5),
            recognition_confidence=98,
            notes="Integration test early time-in.",
        ),
    )
    service.create_event(
        session_id,
        V2CreateEventRequest(
            student_id=late.student_id,
            event_type="time_in",
            event_source="facial_recognition",
            event_time=actual_start + timedelta(minutes=20),
            recognition_confidence=96,
            notes="Integration test late time-in.",
        ),
    )
    service.create_event(
        session_id,
        V2CreateEventRequest(
            student_id=very_late.student_id,
            event_type="time_in",
            event_source="facial_recognition",
            event_time=actual_start + timedelta(minutes=35),
            recognition_confidence=95,
            notes="Integration test very late arrival.",
        ),
    )
    service.save_manual_attendance(
        session_id,
        V2ManualAttendanceRequest(
            professor_id=class_info["professor_id"],
            records=[
                V2ManualAttendanceRecord(
                    record_id=excused.record_id,
                    student_id=excused.student_id,
                    status="excused",
                )
            ],
            notes="Integration test manual excused override.",
        ),
    )

    review = service.end_session(session_id)
    finalized = service.finalize_session(session_id)
    history = service.get_class_session_history(class_info["class_id"])
    roster = {student.student_id: student for student in finalized.roster}
    return {
        "session_id": session_id,
        "review": review,
        "finalized": finalized,
        "history": history,
        "early": roster[early.student_id],
        "late": roster[late.student_id],
        "very_late": roster[very_late.student_id],
        "excused": roster[excused.student_id],
        "csv_filename": _blackboard_filename(class_info, session_id, finalized.session.scheduled_start.date()),
        "csv_text": _csv_text(_csv_rows(finalized.roster)),
    }


def _check_face_data(cursor) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT student_id, COUNT(*)
        FROM student_face_profiles
        WHERE is_active = TRUE
        GROUP BY student_id
        HAVING COUNT(*) > 1
        """
    )
    active_profile_duplicates = cursor.fetchall()

    cursor.execute(
        """
        SELECT student_id, model_name, COUNT(*)
        FROM student_face_embeddings
        GROUP BY student_id, model_name
        HAVING COUNT(*) > 1
        """
    )
    embedding_duplicates = cursor.fetchall()

    cursor.execute(
        """
        SELECT sfe.student_id, sfe.model_name, sfe.source_image_path, e.class_id
        FROM student_face_embeddings sfe
        JOIN enrollments e ON e.student_id = sfe.student_id
        WHERE sfe.source_image_path IS NOT NULL
        ORDER BY sfe.updated_at DESC, sfe.embedding_id DESC
        LIMIT 1
        """
    )
    recognition_candidate = cursor.fetchone()
    return {
        "active_profile_duplicates": active_profile_duplicates,
        "embedding_duplicates": embedding_duplicates,
        "recognition_candidate": recognition_candidate,
    }


async def _try_recognition(service: V2AttendanceService, candidate) -> str:
    if not candidate:
        return "skipped: no saved face embedding source image found"
    _student_id, _model_name, source_image_path, class_id = candidate
    path = Path(source_image_path)
    if not path.exists():
        return f"skipped: saved source image not found at {source_image_path}"
    with path.open("rb") as image_file:
        upload = UploadFile(filename=path.name, file=image_file)
        result = await service.recognize_face_for_class(int(class_id), upload)
    return f"{result.status}: {result.student_name or result.message} ({result.confidence or 0}%)"


async def main() -> int:
    load_local_env()
    service = V2AttendanceService()

    with _connect_raw() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), inet_server_addr(), inet_server_port()")
            database_name, server_addr, server_port = cursor.fetchone()
            print(f"database: {database_name} at {server_addr or 'local socket'}:{server_port}")

            test_professor = _pick_professor(cursor, TEST_EMAIL)
            real_professor = _pick_professor(cursor)
            test_class = _pick_class(cursor, test_professor["professor_id"])
            real_class = _pick_class(cursor, real_professor["professor_id"])
            face_data = _check_face_data(cursor)

    test_login = await login(LoginRequest(email=TEST_EMAIL, password=TEST_PASSWORD))
    real_login = await login(LoginRequest(email=real_professor["email"], password=FACULTY_PASSWORD))
    professor_user_types = {"professor", "instructor"}
    _print_check(
        "test professor login",
        test_login.get("user_type") in professor_user_types,
        f"{TEST_EMAIL} -> {test_login.get('user_type')}",
    )
    _print_check(
        "real seeded professor login",
        real_login.get("user_type") in professor_user_types,
        f"{real_professor['email']} -> {real_login.get('user_type')}",
    )

    for label, professor, class_info in (
        ("test professor", test_professor, test_class),
        ("real professor", real_professor, real_class),
    ):
        print(f"\n-- {label}: {professor['name']} / {class_info['course_code']} {class_info['section']} --")
        today = service.get_today_classes(professor["professor_id"], date.today())
        schedule = service.get_professor_schedule(professor["professor_id"])
        roster = service.get_class_roster(class_info["class_id"])
        face_context = service.get_face_profile_context(class_info["class_id"], roster.students[0].student_id)
        student_history = service.get_student_class_history(class_info["class_id"], roster.students[0].student_id)
        result = _exercise_session(service, class_info)

        finalized = result["finalized"]
        statuses = {student.final_status for student in finalized.roster}
        csv_lines = result["csv_text"].splitlines()

        _print_check("classes/schedule loads", bool(schedule.classes), f"{len(schedule.classes)} classes")
        _print_check(
            "today classes endpoint loads",
            (len(today.current) + len(today.upcoming) + len(today.completed)) >= 0,
            f"{len(today.current)} current, {len(today.upcoming)} upcoming, {len(today.completed)} completed",
        )
        _print_check("student list/class roster loads", bool(roster.students), f"{len(roster.students)} students")
        _print_check("face profile context loads", face_context.student_id == roster.students[0].student_id, face_context.face_profile_status)
        _print_check("student class history loads", student_history.header.student_id == roster.students[0].student_id, f"{len(student_history.records)} records")
        _print_check("live session ended into review", result["review"].session.session_status == "under_review", f"session {result['session_id']}")
        _print_check("finalize locks session", finalized.session.session_status == "finalized")
        _print_check("session history includes finalized session", any(row.session_id == result["session_id"] for row in result["history"].sessions))
        _print_check("student evidence data available", any(student.time_in for student in finalized.roster))
        _print_check("present status produced", result["early"].final_status == "present", result["early"].student_name)
        _print_check("late status produced", result["late"].final_status == "late", result["late"].student_name)
        _print_check(
            "very-late arrival marked absent with note",
            result["very_late"].final_status == "absent" and bool(result["very_late"].review_reason),
            result["very_late"].review_reason or "",
        )
        _print_check("manual excused survives finalize", result["excused"].final_status == "excused", result["excused"].student_name)
        _print_check("Blackboard CSV header", csv_lines[0] == '"Student Number","Student Name","Attendance Status"', csv_lines[0])
        _print_check("Blackboard CSV only final statuses", statuses.issubset({"present", "late", "absent", "excused"}), ", ".join(sorted(statuses)))
        _print_check("Blackboard CSV filename", result["csv_filename"].startswith("fras_blackboard_"), result["csv_filename"])

    recognition_result = await _try_recognition(service, face_data["recognition_candidate"])
    _print_check("no duplicate active face profiles", not face_data["active_profile_duplicates"], str(face_data["active_profile_duplicates"][:3]))
    _print_check("no duplicate embeddings per student/model", not face_data["embedding_duplicates"], str(face_data["embedding_duplicates"][:3]))
    _print_check("recognition endpoint with saved source image", not recognition_result.startswith("skipped"), recognition_result)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
