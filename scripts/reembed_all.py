import os
import json
from services.db import get_connection
from services.settings_service import get_settings_service
from services.face_embeddings import ensure_embeddings_table, extract_embedding_from_image, upsert_student_embedding


def average_vectors(vectors):
    if not vectors:
        return None
    length = len(vectors[0])
    avg = [0.0] * length
    for v in vectors:
        for i in range(length):
            avg[i] += float(v[i])
    n = len(vectors)
    return [x / n for x in avg]


def main():
    dataset_base = os.getenv('DATASET_PATH', '/app/dataset')
    settings = get_settings_service()
    model_name = settings.face_recognition_model

    with get_connection() as conn:
        cursor = conn.cursor()
        ensure_embeddings_table(cursor)

        cursor.execute('SELECT student_id, student_number FROM students')
        rows = cursor.fetchall()

        processed = 0
        stored = 0
        skipped = 0

        for student_id, student_number in rows:
            folder = os.path.join(dataset_base, str(student_number))
            if not os.path.isdir(folder):
                skipped += 1
                print(f"[SKIP] {student_number}: folder missing {folder}")
                continue

            imgs = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.jpg')])
            if not imgs:
                skipped += 1
                print(f"[SKIP] {student_number}: no images in folder")
                continue

            vectors = []
            for img in imgs:
                emb = extract_embedding_from_image(image_path=img, model_name=model_name, enforce_detection=False)
                if emb:
                    vectors.append(emb)

            if not vectors:
                skipped += 1
                print(f"[SKIP] {student_number}: no embeddings extracted")
                continue

            avg = average_vectors(vectors)
            if not avg:
                skipped += 1
                print(f"[SKIP] {student_number}: averaging failed")
                continue

            upsert_student_embedding(cursor=cursor, student_id=student_id, model_name=model_name, embedding=avg, source_image_path=imgs[0])
            conn.commit()
            processed += 1
            stored += 1
            print(f"[OK] {student_number}: averaged embedding stored for student_id={student_id}")

    print('\nRe-embedding complete')
    print(f'Processed: {processed}')
    print(f'Stored: {stored}')
    print(f'Skipped: {skipped}')


if __name__ == '__main__':
    main()
