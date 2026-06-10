from __future__ import annotations

import argparse
import os
import sys

import psycopg2

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env


SESSION_TABLES = [
    "attendance_sessions",
    "student_session_records",
    "attendance_events",
    "professor_overrides",
    "blackboard_sync_logs",
]


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        )
        """,
        (table_name,),
    )
    return bool(cursor.fetchone()[0])


def count_rows(cursor, table_name: str) -> int:
    if not table_exists(cursor, table_name):
        return 0
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cursor.fetchone()[0])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clear FRAS V2 session history/activity without deleting users, "
            "professors, courses, rooms, classes, students, enrollments, or face data."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Actually clear V2 attendance sessions, records, events, overrides, and CSV sync logs.",
    )
    args = parser.parse_args(argv)

    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            counts = {table: count_rows(cursor, table) for table in SESSION_TABLES}
            for table, count in counts.items():
                print(f"{table}: {count}")

            if not args.force:
                print("Dry run only. Re-run with --force to clear V2 session history/activity.")
                return 0

            cursor.execute(
                """
                TRUNCATE TABLE
                    blackboard_sync_logs,
                    professor_overrides,
                    attendance_events,
                    student_session_records,
                    attendance_sessions
                RESTART IDENTITY CASCADE
                """
            )

    print("V2 session history/activity cleared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
