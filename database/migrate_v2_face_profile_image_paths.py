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


def active_front_image(student_dir: Path) -> Path | None:
    active_dir = student_dir / "active"
    if not active_dir.exists():
        return None
    candidates = sorted(active_dir.glob("front.*"), key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update V2 face profile DB paths to dataset/v2_face_profiles/{student_number}/active/front.*."
    )
    parser.add_argument("--database-url", help="Override DATABASE_URL for this run.")
    parser.add_argument(
        "--dataset-path",
        default=os.environ.get("DATASET_PATH", "dataset"),
        help="Dataset path. Defaults to DATASET_PATH or ./dataset.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without updating the database.")
    args = parser.parse_args(argv)

    load_local_env()
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    dataset_path = Path(args.dataset_path)
    if not dataset_path.is_absolute():
        dataset_path = ROOT_DIR / dataset_path
    face_root = dataset_path / "v2_face_profiles"
    if not face_root.exists():
        print(f"Missing face profile folder: {face_root}")
        return 1

    updates: list[tuple[str, str]] = []
    for student_dir in sorted(item for item in face_root.iterdir() if item.is_dir()):
        image_path = active_front_image(student_dir)
        if image_path:
            updates.append((student_dir.name, str(image_path)))

    print(f"active face images found: {len(updates)}")
    if args.dry_run:
        for student_number, image_path in updates:
            print(f"{student_number} -> {image_path}")
        print("Dry run only. Re-run without --dry-run to update database paths.")
        return 0

    updated_profiles = 0
    updated_embeddings = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        for student_number, image_path in updates:
            cursor.execute(
                """
                SELECT student_id
                FROM students
                WHERE student_number = ?
                """,
                (student_number,),
            )
            row = cursor.fetchone()
            if not row:
                print(f"Skipping {student_number}: student not found in database.")
                continue
            student_id = int(row[0])

            cursor.execute(
                """
                UPDATE student_face_profiles
                SET face_image_path = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = ?
                  AND is_active = TRUE
                """,
                (image_path, student_id),
            )
            updated_profiles += max(cursor.rowcount or 0, 0)

            cursor.execute(
                """
                UPDATE student_face_embeddings
                SET source_image_path = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = ?
                """,
                (image_path, student_id),
            )
            updated_embeddings += max(cursor.rowcount or 0, 0)

    print(f"updated active profile paths: {updated_profiles}")
    print(f"updated embedding source paths: {updated_embeddings}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
