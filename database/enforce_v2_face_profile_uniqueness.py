from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.db import get_connection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce one active FRAS V2 face profile per student. "
            "Keeps the newest active profile and deactivates older active duplicates."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report duplicate active profile groups without changing rows or creating the index.",
    )
    args = parser.parse_args(argv)

    load_local_env()
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set.")
        return 1

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT student_id, COUNT(*) AS active_count
            FROM student_face_profiles
            WHERE is_active = TRUE
            GROUP BY student_id
            HAVING COUNT(*) > 1
            ORDER BY active_count DESC, student_id
            """
        )
        duplicates = cursor.fetchall()
        print(f"students with duplicate active profiles: {len(duplicates)}")
        for student_id, active_count in duplicates:
            print(f"student_id={student_id} active_profiles={active_count}")

        if args.dry_run:
            print("Dry run only. Re-run without --dry-run to enforce uniqueness.")
            return 0

        cursor.execute(
            """
            UPDATE student_face_profiles
            SET is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE face_profile_id IN (
                SELECT face_profile_id
                FROM (
                    SELECT
                        face_profile_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY student_id
                            ORDER BY COALESCE(updated_at, registered_at) DESC, face_profile_id DESC
                        ) AS row_number
                    FROM student_face_profiles
                    WHERE is_active = TRUE
                ) ranked_profiles
                WHERE row_number > 1
            )
            """
        )
        deactivated_count = cursor.rowcount if cursor.rowcount is not None else 0

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_face_profile_per_student
            ON student_face_profiles(student_id)
            WHERE is_active = TRUE
            """
        )

    print(f"deactivated duplicate active profiles: {deactivated_count}")
    print("unique active face profile index is enforced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
