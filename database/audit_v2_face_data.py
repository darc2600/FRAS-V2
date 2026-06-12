from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.db import get_connection


DEFAULT_NAMES = ["Adams", "Tan", "Reyes", "Cruz"]


def parse_embedding_json(embedding_json: str) -> list[float] | None:
    try:
        parsed = json.loads(embedding_json)
        if not isinstance(parsed, list):
            return None
        return [float(value) for value in parsed]
    except Exception:
        return None


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return -1.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return -1.0
    return dot_product / (norm_a * norm_b)


def rows_as_dicts(cursor, rows):
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def print_section(title: str) -> None:
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))


def print_rows(rows: list[dict], empty_message: str) -> None:
    if not rows:
        print(empty_message)
        return
    for row in rows:
        print(" | ".join(f"{key}={value}" for key, value in row.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit FRAS V2 face profile and embedding data without modifying the database."
    )
    parser.add_argument(
        "--names",
        nargs="*",
        default=DEFAULT_NAMES,
        help="Last names or search terms to inspect. Default: Adams Tan Reyes Cruz.",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.82,
        help="Report active embedding pairs at or above this cosine similarity.",
    )
    args = parser.parse_args(argv)

    load_local_env()
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set.")
        return 1

    with get_connection() as conn:
        cursor = conn.cursor()

        print_section("Active Face Profiles For Selected Students")
        like_terms = [f"%{name}%" for name in args.names]
        where_clause = " OR ".join(["LOWER(s.last_name) LIKE LOWER(?)" for _ in like_terms])
        cursor.execute(
            f"""
            SELECT
                s.student_id,
                s.student_number,
                s.last_name,
                s.first_name,
                fp.face_profile_id,
                fp.is_active,
                fp.face_image_path,
                fp.registered_at,
                fp.updated_at
            FROM students s
            LEFT JOIN student_face_profiles fp ON fp.student_id = s.student_id
            WHERE {where_clause}
            ORDER BY s.last_name, s.first_name, fp.is_active DESC, fp.updated_at DESC
            """,
            like_terms,
        )
        print_rows(rows_as_dicts(cursor, cursor.fetchall()), "No matching students or profiles found.")

        print_section("Active Embeddings For Selected Students")
        cursor.execute(
            f"""
            SELECT
                s.student_id,
                s.student_number,
                s.last_name,
                s.first_name,
                sfe.embedding_id,
                sfe.model_name,
                sfe.source_image_path,
                sfe.updated_at
            FROM students s
            LEFT JOIN student_face_embeddings sfe ON sfe.student_id = s.student_id
            WHERE {where_clause}
            ORDER BY s.last_name, s.first_name, sfe.updated_at DESC
            """,
            like_terms,
        )
        print_rows(rows_as_dicts(cursor, cursor.fetchall()), "No matching embeddings found.")

        print_section("Duplicate Active Profile Counts")
        cursor.execute(
            """
            SELECT student_id, COUNT(*) AS active_profile_count
            FROM student_face_profiles
            WHERE is_active = TRUE
            GROUP BY student_id
            HAVING COUNT(*) > 1
            ORDER BY active_profile_count DESC, student_id
            """
        )
        print_rows(rows_as_dicts(cursor, cursor.fetchall()), "No duplicate active face profiles found.")

        print_section("Duplicate Embedding Rows Per Student/Model")
        cursor.execute(
            """
            SELECT student_id, model_name, COUNT(*) AS embedding_count
            FROM student_face_embeddings
            GROUP BY student_id, model_name
            HAVING COUNT(*) > 1
            ORDER BY embedding_count DESC, student_id, model_name
            """
        )
        print_rows(rows_as_dicts(cursor, cursor.fetchall()), "No duplicate embedding rows found for the same student/model.")

        print_section("Reused Source Image Paths Across Students")
        cursor.execute(
            """
            SELECT
                source_image_path,
                COUNT(DISTINCT student_id) AS student_count
            FROM student_face_embeddings
            WHERE source_image_path IS NOT NULL
            GROUP BY source_image_path
            HAVING COUNT(DISTINCT student_id) > 1
            ORDER BY student_count DESC, source_image_path
            """
        )
        print_rows(rows_as_dicts(cursor, cursor.fetchall()), "No source image paths are reused across students.")

        print_section("Exact Duplicate Embeddings Across Students")
        cursor.execute(
            """
            SELECT
                s.student_id,
                s.student_number,
                s.last_name,
                s.first_name,
                sfe.embedding_id,
                sfe.model_name,
                sfe.embedding_json,
                sfe.source_image_path
            FROM student_face_embeddings sfe
            JOIN students s ON s.student_id = sfe.student_id
            ORDER BY sfe.model_name, s.student_id
            """
        )
        embedding_rows = rows_as_dicts(cursor, cursor.fetchall())
        by_hash: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in embedding_rows:
            digest = hashlib.sha256(str(row["embedding_json"]).encode("utf-8")).hexdigest()
            by_hash[(str(row["model_name"]), digest)].append(row)

        duplicate_groups = [
            rows for rows in by_hash.values()
            if len({row["student_id"] for row in rows}) > 1
        ]
        if not duplicate_groups:
            print("No exact duplicate embeddings found across students.")
        else:
            for index, rows in enumerate(duplicate_groups, start=1):
                print(f"Duplicate group {index}:")
                for row in rows:
                    print(
                        f"  student_id={row['student_id']} "
                        f"name={row['last_name']}, {row['first_name']} "
                        f"embedding_id={row['embedding_id']} source={row['source_image_path']}"
                    )

        print_section("High Similarity Active Embedding Pairs")
        active_vectors = []
        cursor.execute(
            """
            SELECT
                s.student_id,
                s.student_number,
                s.last_name,
                s.first_name,
                sfe.embedding_id,
                sfe.model_name,
                sfe.embedding_json,
                sfe.source_image_path,
                fp.face_profile_id
            FROM student_face_embeddings sfe
            JOIN students s ON s.student_id = sfe.student_id
            JOIN student_face_profiles fp ON fp.student_id = s.student_id
                AND fp.is_active = TRUE
            ORDER BY sfe.model_name, s.student_id
            """
        )
        for row in rows_as_dicts(cursor, cursor.fetchall()):
            vector = parse_embedding_json(str(row["embedding_json"]))
            if vector:
                active_vectors.append((row, vector))

        found_pair = False
        for left_index, (left, left_vector) in enumerate(active_vectors):
            for right, right_vector in active_vectors[left_index + 1:]:
                if left["model_name"] != right["model_name"]:
                    continue
                similarity = cosine_similarity(left_vector, right_vector)
                if similarity >= args.similarity_threshold:
                    found_pair = True
                    print(
                        f"similarity={similarity:.4f} model={left['model_name']} | "
                        f"{left['student_id']} {left['last_name']}, {left['first_name']} "
                        f"(embedding={left['embedding_id']}, profile={left['face_profile_id']}) <-> "
                        f"{right['student_id']} {right['last_name']}, {right['first_name']} "
                        f"(embedding={right['embedding_id']}, profile={right['face_profile_id']})"
                    )
        if not found_pair:
            print(f"No active embedding pairs at or above {args.similarity_threshold:.2f}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
