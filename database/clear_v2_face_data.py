from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import psycopg2

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env


ROOT_DIR = Path(__file__).resolve().parents[1]


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


def delete_tree(path: Path) -> int:
    if not path.exists():
        return 0
    file_count = sum(1 for item in path.rglob("*") if item.is_file())
    shutil.rmtree(path)
    return file_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clear FRAS V2 face registration data without deleting professors, "
            "classes, students, enrollments, sessions, or schedules."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Actually delete face profiles, face embeddings, and saved V2 face image files.",
    )
    parser.add_argument(
        "--keep-images",
        action="store_true",
        help="Clear database face records but keep saved image files on disk.",
    )
    args = parser.parse_args(argv)

    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    dataset_base = Path(os.environ.get("DATASET_PATH", "dataset"))
    if not dataset_base.is_absolute():
        dataset_base = ROOT_DIR / dataset_base
    face_dir = dataset_base / "v2_face_profiles"

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            profile_count = count_rows(cursor, "student_face_profiles")
            embedding_count = count_rows(cursor, "student_face_embeddings")

            print(f"student_face_profiles rows: {profile_count}")
            print(f"student_face_embeddings rows: {embedding_count}")
            print(f"face image folder: {face_dir}")

            if not args.force:
                print("Dry run only. Re-run with --force to clear V2 face data.")
                return 0

            if table_exists(cursor, "student_face_profiles"):
                cursor.execute("DELETE FROM student_face_profiles")
            if table_exists(cursor, "student_face_embeddings"):
                cursor.execute("DELETE FROM student_face_embeddings")

    deleted_files = 0
    if not args.keep_images:
        deleted_files = delete_tree(face_dir)

    print("V2 face data cleared.")
    print(f"Deleted image files: {deleted_files}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
