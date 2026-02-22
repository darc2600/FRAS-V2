import os

from services.db import get_connection
from services.settings_service import get_settings_service
from services.face_embeddings import (
    ensure_embeddings_table,
    extract_embedding_from_image,
    upsert_student_embedding,
)


def _first_jpg_from_folder(folder_path: str):
    if not folder_path or not os.path.isdir(folder_path):
        return None
    files = sorted(
        [
            os.path.join(folder_path, file_name)
            for file_name in os.listdir(folder_path)
            if file_name.lower().endswith('.jpg')
        ]
    )
    return files[0] if files else None


def main():
    settings = get_settings_service()
    model_name = settings.face_recognition_model

    with get_connection() as conn:
        cursor = conn.cursor()
        ensure_embeddings_table(cursor)

        cursor.execute(
            '''
            SELECT student_id, student_number, face_data_path
            FROM students
            ORDER BY student_id
            '''
        )
        students = cursor.fetchall()

        processed = 0
        stored = 0
        skipped = 0

        for student_id, student_number, face_data_path in students:
            processed += 1

            # Normalize potential Windows-style backslashes in stored paths
            if face_data_path:
                folder_path = face_data_path.replace('\\', '/')
            else:
                folder_path = os.path.join('dataset', str(student_number))

            image_path = _first_jpg_from_folder(folder_path)
            if not image_path:
                skipped += 1
                print(f"[SKIP] student_id={student_id} student_number={student_number}: no .jpg found in {folder_path}")
                continue

            embedding = extract_embedding_from_image(
                image_path=image_path,
                model_name=model_name,
                enforce_detection=False,
            )
            if not embedding:
                skipped += 1
                print(f"[SKIP] student_id={student_id} student_number={student_number}: embedding extraction failed")
                continue

            upsert_student_embedding(
                cursor=cursor,
                student_id=student_id,
                model_name=model_name,
                embedding=embedding,
                source_image_path=image_path,
            )
            stored += 1
            print(f"[OK] student_id={student_id} student_number={student_number}: embedding saved")

        conn.commit()

    print("\nBackfill complete")
    print(f"Processed: {processed}")
    print(f"Stored:    {stored}")
    print(f"Skipped:   {skipped}")


if __name__ == '__main__':
    main()
