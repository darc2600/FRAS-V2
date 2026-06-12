import os
import json
from typing import List, Optional, Tuple

from deepface import DeepFace


def ensure_embeddings_table(cursor) -> None:
    # Create SQL compatible with the active database dialect.
    db_url = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
    if db_url.startswith('sqlite'):
        create_sql = '''
        CREATE TABLE IF NOT EXISTS student_face_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            source_image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, model_name)
        )
        '''
    else:
        # PostgreSQL compatible definition
        create_sql = '''
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
        '''

    cursor.execute(create_sql)


def extract_embedding_from_image(
    image_path: str,
    model_name: str,
    enforce_detection: bool = False,
) -> Optional[List[float]]:
    try:
        reps = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            enforce_detection=enforce_detection,
        )
        if not reps:
            return None

        first = reps[0] if isinstance(reps, list) else reps
        embedding = first.get("embedding") if isinstance(first, dict) else None

        if not embedding or not isinstance(embedding, list):
            return None

        return [float(v) for v in embedding]
    except Exception:
        return None


def extract_embeddings_from_image(
    image_path: str,
    model_name: str,
    enforce_detection: bool = True,
) -> list[list[float]]:
    """Return all detected face embeddings in image order.

    V2 recognition deliberately uses only the first detected face after this
    extraction so multi-face frames do not silently register multiple people.
    """
    try:
        reps = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            enforce_detection=enforce_detection,
        )
        if not reps:
            return []

        normalized_reps = reps if isinstance(reps, list) else [reps]
        embeddings: list[list[float]] = []
        for item in normalized_reps:
            embedding = item.get("embedding") if isinstance(item, dict) else None
            if embedding and isinstance(embedding, list):
                embeddings.append([float(v) for v in embedding])
        return embeddings
    except Exception:
        return []


def upsert_student_embedding(
    cursor,
    student_id: int,
    model_name: str,
    embedding: List[float],
    source_image_path: Optional[str] = None,
) -> None:
    embedding_json = json.dumps(embedding)

    cursor.execute(
        '''
        INSERT INTO student_face_embeddings (student_id, model_name, embedding_json, source_image_path)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (student_id, model_name) DO UPDATE SET
            embedding_json = excluded.embedding_json,
            source_image_path = excluded.source_image_path,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (student_id, model_name, embedding_json, source_image_path),
    )


def load_enrolled_embeddings(cursor, class_id: int, model_name: str) -> List[Tuple[int, str, str]]:
    cursor.execute(
        '''
        SELECT e.student_id, s.last_name, sfe.embedding_json
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        JOIN student_face_embeddings sfe ON sfe.student_id = e.student_id
        WHERE e.class_id = ? AND sfe.model_name = ?
        ''',
        (class_id, model_name),
    )
    return cursor.fetchall()


def load_active_enrolled_embeddings(cursor, class_id: int, model_name: str) -> List[Tuple[int, int, str, str, str, Optional[str], Optional[int]]]:
    cursor.execute(
        '''
        SELECT
            sfe.embedding_id,
            e.student_id,
            s.first_name,
            s.last_name,
            sfe.embedding_json,
            sfe.source_image_path,
            fp.face_profile_id
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        JOIN student_face_embeddings sfe ON sfe.student_id = e.student_id
        JOIN student_face_profiles fp ON fp.student_id = e.student_id
            AND fp.is_active = TRUE
            AND fp.face_profile_id = (
                SELECT fp_latest.face_profile_id
                FROM student_face_profiles fp_latest
                WHERE fp_latest.student_id = e.student_id
                  AND fp_latest.is_active = TRUE
                ORDER BY COALESCE(fp_latest.updated_at, fp_latest.registered_at) DESC,
                    fp_latest.face_profile_id DESC
                LIMIT 1
            )
        WHERE e.class_id = ?
          AND e.enrollment_status = 'active'
          AND sfe.model_name = ?
        ORDER BY s.last_name, s.first_name, sfe.embedding_id
        ''',
        (class_id, model_name),
    )
    return cursor.fetchall()


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return -1.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5

    if norm_a == 0.0 or norm_b == 0.0:
        return -1.0

    return dot_product / (norm_a * norm_b)


def similarity_threshold_from_distance_threshold(distance_threshold: float) -> float:
    try:
        distance = float(distance_threshold)
    except Exception:
        distance = 0.6

    similarity_threshold = 1.0 - distance
    if similarity_threshold < 0.0:
        return 0.0
    if similarity_threshold > 1.0:
        return 1.0
    return similarity_threshold


def parse_embedding_json(embedding_json: str) -> Optional[List[float]]:
    try:
        parsed = json.loads(embedding_json)
        if not isinstance(parsed, list):
            return None
        return [float(v) for v in parsed]
    except Exception:
        return None
