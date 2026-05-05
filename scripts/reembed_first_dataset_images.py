from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.face_embeddings import (
    ensure_embeddings_table,
    extract_embedding_from_image,
    upsert_student_embedding,
)
from services.settings_service import get_settings_service


DB_PATH = ROOT / "attendance.db"
DATASET_PATH = ROOT / "dataset"


def first_image(folder: Path) -> Path | None:
    candidates = sorted(
        [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ],
        key=lambda path: path.name.lower(),
    )
    return candidates[0] if candidates else None


def main() -> None:
    os.chdir(ROOT)
    settings = get_settings_service()
    model_name = settings.face_recognition_model

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        ensure_embeddings_table(cursor)
        cursor.execute("DELETE FROM student_face_embeddings")

        cursor.execute(
            """
            SELECT student_id, student_number
            FROM students
            ORDER BY student_id
            """
        )
        students = cursor.fetchall()

        processed = 0
        stored = 0
        skipped = 0

        for student_id, student_number in students:
            processed += 1
            folder = DATASET_PATH / str(student_number)
            image_path = first_image(folder) if folder.is_dir() else None
            if image_path is None:
                skipped += 1
                print(f"[SKIP] {student_number}: no dataset image found")
                continue

            embedding = extract_embedding_from_image(
                image_path=str(image_path),
                model_name=model_name,
                enforce_detection=False,
            )
            if not embedding:
                skipped += 1
                print(f"[SKIP] {student_number}: embedding extraction failed")
                continue

            source_path = image_path.relative_to(ROOT).as_posix()
            upsert_student_embedding(
                cursor=cursor,
                student_id=student_id,
                model_name=model_name,
                embedding=embedding,
                source_image_path=source_path,
            )
            stored += 1
            print(f"[OK] {student_number}: {source_path}")

        conn.commit()

    print("\nEmbedding reset complete")
    print(f"Processed students: {processed}")
    print(f"Stored embeddings:  {stored}")
    print(f"Skipped students:   {skipped}")
    print(f"Model:              {model_name}")


if __name__ == "__main__":
    main()
