from __future__ import annotations

import asyncio
import os
import sys
from datetime import date
from pathlib import Path

import psycopg2

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env

from api.auth import LoginRequest, login
from v2.service import V2AttendanceService


def main() -> int:
    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_schema(), inet_server_addr(), inet_server_port(), current_user")
            database_name, schema_name, server_addr, server_port, user_name = cursor.fetchone()
            print(f"database: {database_name}")
            print(f"schema: {schema_name}")
            print(f"server: {server_addr or 'local socket'}:{server_port}")
            print(f"user: {user_name}")

            for table in ("users", "professors", "courses", "rooms", "students", "classes", "enrollments"):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                print(f"{table}: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM classes WHERE term = 'SY 2025-3RD'")
            print(f"SY 2025-3RD classes: {cursor.fetchone()[0]}")
            cursor.execute("SELECT COUNT(*) FROM classes WHERE term = 'TEST'")
            print(f"TEST classes: {cursor.fetchone()[0]}")
            cursor.execute("SELECT COUNT(*) FROM rooms WHERE UPPER(room_number) = 'ONLINE'")
            print(f"ONLINE room rows: {cursor.fetchone()[0]}")

            cursor.execute(
                """
                SELECT email
                FROM professors
                WHERE faculty_number LIKE 'DOCX-%'
                ORDER BY professor_id
                LIMIT 1
                """
            )
            faculty_email = cursor.fetchone()[0]

    faculty_login = asyncio.run(login(LoginRequest(email=faculty_email, password="password")))
    test_login = asyncio.run(login(LoginRequest(email="test.professor@fras.local", password="password123")))
    print(f"faculty login ok: {faculty_email} -> {faculty_login['user_type']}")
    print(f"test login ok: test.professor@fras.local -> {test_login['user_type']}")

    service = V2AttendanceService()
    professors = service.list_professors()
    test_professor = next(item for item in professors if item.email == "test.professor@fras.local")
    today = service.get_today_classes(test_professor.professor_id, date(2026, 6, 8))
    schedule = service.get_professor_schedule(test_professor.professor_id)
    first_class = schedule.classes[0]
    roster = service.get_class_roster(first_class.class_id)

    print(
        "test today classes: "
        f"current={len(today.current)} upcoming={len(today.upcoming)} completed={len(today.completed)}"
    )
    print(f"test schedule classes: {len(schedule.classes)}")
    print(f"first test class roster students: {len(roster.students)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
