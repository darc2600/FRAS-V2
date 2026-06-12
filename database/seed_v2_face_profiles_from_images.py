from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from database.init_v2_database import ROOT_DIR, load_local_env
except ImportError:
    from init_v2_database import ROOT_DIR, load_local_env

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.db import get_connection


DEFAULT_FACE_ROOT = ROOT_DIR / "dataset" / "v2_face_profiles"
DEFAULT_MODEL_NAME = "ArcFace"
DEFAULT_SKIP_STUDENT_NUMBERS = {
    "2025103053",  # failed registration/recognition during local testing
    "2025103056",  # registered but ambiguous during local testing
    "2025103069",  # failed registration/recognition during local testing
}


def ensure_embeddings_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS student_face_embeddings (
            embedding_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            source_image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, model_name)
        )
        """
    )


def find_active_front_image(student_dir: Path) -> Path | None:
    active_dir = student_dir / "active"
    for extension in ("jpg", "jpeg", "png", "webp"):
        image_path = active_dir / f"front.{extension}"
        if image_path.exists():
            return image_path
    return None


def get_student_id(cursor, student_number: str) -> int | None:
    cursor.execute(
        """
        SELECT student_id
        FROM students
        WHERE student_number = ?
          AND is_active = TRUE
        """,
        (student_number,),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else None


def replace_face_profile(
    cursor,
    student_id: int,
    image_path: Path,
    model_name: str,
    embedding: list[float],
) -> int:
    embedding_json = json.dumps(embedding)
    normalized_path = image_path.as_posix()

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
        (student_id, normalized_path, embedding_json, model_name),
    )
    face_profile_id = int(cursor.fetchone()[0])

    cursor.execute(
        """
        INSERT INTO student_face_embeddings (
            student_id,
            model_name,
            embedding_json,
            source_image_path
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT (student_id, model_name) DO UPDATE SET
            embedding_json = excluded.embedding_json,
            source_image_path = excluded.source_image_path,
            updated_at = CURRENT_TIMESTAMP
        """,
        (student_id, model_name, embedding_json, normalized_path),
    )
    return face_profile_id


def parse_skip_values(values: list[str], include_problematic: bool) -> set[str]:
    skipped = set() if include_problematic else set(DEFAULT_SKIP_STUDENT_NUMBERS)
    for value in values:
        for student_number in value.split(","):
            cleaned = student_number.strip()
            if cleaned:
                skipped.add(cleaned)
    return skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Seed FRAS V2 face profiles and embeddings from saved "
            "dataset/v2_face_profiles/{student_number}/active/front.* images."
        )
    )
    parser.add_argument("--face-root", type=Path, default=DEFAULT_FACE_ROOT)
    parser.add_argument("--model-name", default=os.getenv("FRAS_FACE_MODEL", DEFAULT_MODEL_NAME))
    parser.add_argument("--skip", action="append", default=[], help="Student number to skip. Can be repeated or comma-separated.")
    parser.add_argument(
        "--include-problematic",
        action="store_true",
        help="Do not automatically skip locally flagged problematic photos.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would be seeded without writing to the database.")
    args = parser.parse_args(argv)

    face_root = args.face_root.resolve()
    if not face_root.exists():
        print(f"Missing face profile folder: {face_root}")
        return 1

    skip_student_numbers = parse_skip_values(args.skip, include_problematic=args.include_problematic)

    load_local_env()
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL is not set.")
        return 1

    seeded = 0
    skipped = 0
    failed = 0
    missing_students = 0

    with get_connection() as conn:
        from services.face_embeddings import extract_embeddings_from_image

        cursor = conn.cursor()
        ensure_embeddings_table(cursor)

        for student_dir in sorted(path for path in face_root.iterdir() if path.is_dir()):
            student_number = student_dir.name
            image_path = find_active_front_image(student_dir)
            if not image_path:
                continue

            if student_number in skip_student_numbers:
                print(f"SKIP {student_number}: marked for retake/manual registration")
                skipped += 1
                continue

            student_id = get_student_id(cursor, student_number)
            if student_id is None:
                print(f"MISS {student_number}: no active student row in database")
                missing_students += 1
                continue

            embeddings = extract_embeddings_from_image(
                str(image_path),
                model_name=args.model_name,
                enforce_detection=True,
            )
            if len(embeddings) != 1:
                print(f"FAIL {student_number}: expected exactly one detected face, got {len(embeddings)}")
                failed += 1
                continue

            if args.dry_run:
                print(f"READY {student_number}: {image_path.relative_to(ROOT_DIR)}")
                seeded += 1
                continue

            face_profile_id = replace_face_profile(
                cursor=cursor,
                student_id=student_id,
                image_path=image_path,
                model_name=args.model_name,
                embedding=embeddings[0],
            )
            print(f"SEEDED {student_number}: face_profile_id={face_profile_id}")
            seeded += 1

        if args.dry_run:
            conn.rollback()

    print("")
    print(f"Face root: {face_root}")
    print(f"Model: {args.model_name}")
    print(f"Seeded/ready: {seeded}")
    print(f"Skipped for retake: {skipped}")
    print(f"Failed extraction: {failed}")
    print(f"Missing students: {missing_students}")
    return 1 if failed or missing_students else 0


if __name__ == "__main__":
    sys.exit(main())
