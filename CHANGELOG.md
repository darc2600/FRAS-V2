## Changelog

All notable changes for the current patch.

### 2026-02-24 — Postgres migration fixes
- `services/db.py`: Added `PGCursorWrapper` conversion of Postgres `date`/`datetime` to ISO strings to avoid Pydantic ResponseValidationError when FastAPI returns DB values.
- `api/admin.py`: Defensive normalization/stringification of `created_at`/`updated_at` fields and added exception logging for the face-embedding coverage endpoint.
- `services/face_embeddings.py`: Dialect-aware `CREATE TABLE` for `student_face_embeddings` (uses `AUTOINCREMENT` for SQLite and `SERIAL`/`TIMESTAMP` for Postgres).

Notes:
- These changes were copied into the running container and validated on the VPS; the `/api/admin/face-embedding-coverage` endpoint no longer raises the AUTOINCREMENT syntax error on Postgres.
