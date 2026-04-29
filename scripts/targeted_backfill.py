import os
from services.db import get_connection
from services.settings_service import get_settings_service
from services.face_embeddings import (
    ensure_embeddings_table,
    extract_embedding_from_image,
    upsert_student_embedding,
)


def main():
    settings = get_settings_service()
    model_name = settings.face_recognition_model

    dataset_base = os.getenv('DATASET_PATH', 'dataset')
    folders = sorted([d for d in os.listdir(dataset_base) if os.path.isdir(os.path.join(dataset_base, d))])

    with get_connection() as conn:
        cursor = conn.cursor()
        ensure_embeddings_table(cursor)

        processed = 0
        stored = 0
        skipped = 0

        for folder in folders:
            folder_path = os.path.join(dataset_base, folder)
            # pick first jpg
            imgs = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.jpg')])
            if not imgs:
                skipped += 1
                print(f"[SKIP] {folder}: no .jpg in {folder_path}")
                continue

            # find student_id from student_number == folder
            cursor.execute('SELECT student_id FROM students WHERE student_number = ?', (folder,))
            row = cursor.fetchone()
            if not row:
                skipped += 1
                print(f"[SKIP] {folder}: no student record")
                continue
            student_id = row[0]

            embedding = extract_embedding_from_image(
                image_path=imgs[0],
                model_name=model_name,
                enforce_detection=False,
            )
            processed += 1
            if not embedding:
                skipped += 1
                print(f"[SKIP] {folder}: embedding extraction failed")
                continue

            upsert_student_embedding(
                cursor=cursor,
                student_id=student_id,
                model_name=model_name,
                embedding=embedding,
                source_image_path=imgs[0],
            )
            conn.commit()
            stored += 1
            print(f"[OK] {folder}: embedding stored for student_id={student_id}")

    print('\nTargeted backfill complete')
    print(f'Processed: {processed}')
    print(f'Stored:    {stored}')
    print(f'Skipped:   {skipped}')


if __name__ == '__main__':
    main()
