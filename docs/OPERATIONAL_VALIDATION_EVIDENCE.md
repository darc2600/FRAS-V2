# Operational Validation Evidence

This document summarizes the measurable operational validation evidence currently available in the FRAS repository and documented deployment inspection artifacts. It is based on the recognition implementation, API smoke-test outputs, local database inspection, migration/deployment scripts, Docker/Nginx configuration, and the existing live-deployment dataset statistics document.

Inspection date: May 19, 2026

## 1. Recognition Pipeline Validation Evidence

| Validation item | Evidence currently available | Finding |
|---|---|---|
| Successful recognition logs | `tools/full_flow_attendance_test_results.json` records `POST /api/recognize` returning `status: success`, student `1`, attendance status `Present`, followed by `GET /api/attendance` returning the inserted attendance row. The local `attendance.db` also contains 33 attendance log rows whose notes begin with `Face recognized at`. The live deployment statistics document reports 248 recognized attendance entries identified by `Face recognized` notes. | Supported by saved test output, local database rows, and deployment statistics. |
| Failed recognition logs | `tools/smoke_test_files_and_attendance_results.json` records `POST /api/recognize` returning `status: failed` and message `No match found`. However, failed recognition attempts are not persisted in a dedicated recognition-attempt table. | Failed API response evidence exists, but no structured failed-recognition log table exists. |
| Duplicate attendance prevention | `repositories/recognition_repo.py` checks the latest attendance row for the same student, class, and date, then blocks insertion when it is within `attendance_buffer_minutes`. No saved test artifact was found that intentionally performs a second recognition and proves the duplicate block response. | Implemented, but no direct saved duplicate-prevention test result was found. |
| Schedule validation failures | `repositories/recognition_repo.py` rejects recognition when the current Manila day does not match the class day or when the current time is outside the class start/end window. No saved test artifact was found that intentionally triggers and records these schedule failure responses. | Implemented, but no direct saved failure test result was found. |
| Fallback DeepFace verification | `repositories/recognition_repo.py` attempts embedding-first recognition, then falls back to `DeepFace.verify()` against enrolled students' dataset images when embedding matching does not produce a valid match. Runtime debug printing exists for fallback comparison and DeepFace results. No saved test artifact proves that the fallback path was triggered during an actual run. | Implemented, but fallback execution is not directly evidenced by saved logs/results. |
| Configurable thresholds | `services/settings_service.py`, `config/default_settings.py`, and current database settings show configurable `recognition_threshold`, `face_recognition_model`, `attendance_buffer_minutes`, `late_threshold_minutes`, `absent_threshold_minutes`, `recognition_timeout_seconds`, and related settings. Local inspection found `recognition_threshold = 0.65`, `attendance_buffer_minutes = 2`, and `recognition_timeout_seconds = 30`. | Supported. |
| Recognition timing or durations | `recognition_timeout_seconds` is configurable, and smoke-test scripts use request timeouts. No persisted response-duration, recognition elapsed-time, confidence, distance, or similarity metric table was found. The deployment statistics document also states that no structured timing columns were found. | Timeout configuration exists, but measured durations are not available. |
| Recognition API responses logged during testing | Saved JSON artifacts include recognition responses for success and failure: `tools/full_flow_attendance_test_results.json` and `tools/smoke_test_files_and_attendance_results.json`. | Supported by saved API response artifacts. |

Measurable recognition evidence currently available:

- A full positive recognition workflow: schedule creation, multipart registration, successful recognition, and attendance retrieval.
- A negative recognition response: `No match found`.
- Local database evidence of 50 attendance rows, including 33 rows with `Face recognized at` notes.
- Deployment-level summary evidence of 265 attendance logs and 248 recognized attendance entries.
- No structured persisted recognition attempt log, failed-recognition table, confidence column, similarity column, or duration column was found.

## 2. Backend And API Testing Evidence

| Validation item | Evidence currently available | Finding |
|---|---|---|
| Tested API endpoints | `tools/api_test_report.md`, `tools/smoke_test_results.json`, and `tools/smoke_test_extended_results.json` show OpenAPI access plus GET testing for rooms, floors, attendance, courses, instructors, students, classes, debug face-embedding coverage, admin users, admin analytics, system settings, and support tickets. | Supported. |
| Successful request/response validation | Smoke-test outputs include HTTP statuses, `ok` flags, content types, item counts, response keys, and response bodies. | Supported. |
| Multipart upload testing | `tools/full_flow_attendance_test_results.json` records multipart `/api/registration` and multipart `/api/recognize`. `tools/smoke_test_files_and_attendance_results.json` records multipart `/api/registration`, `/api/capture`, and `/api/recognize`. | Supported. |
| JWT authentication testing | `tools/smoke_test_results.json` records successful superadmin login, token retrieval, bearer token storage, and authenticated retry behavior. | Supported. |
| Role-based access testing | Admin GET endpoints returned `403` without authentication and `200` with superadmin authentication in `tools/smoke_test_results.json` and `tools/smoke_test_extended_results.json`. | Supported for protected admin endpoints. |
| Attendance logging verification | `tools/full_flow_attendance_test_results.json` verifies that recognition was followed by attendance retrieval containing a `Present` record. `tests/test_e2e_attendance.py` also asserts that an attendance log exists in the database after successful recognition. | Supported. |
| Database insertion validation | Saved results show create/delete user, support ticket create/update/reply, schedule create/delete, registration, capture, recognition, and attendance retrieval. `tests/test_e2e_attendance.py` directly checks the `attendance_logs` table. | Supported. |
| Report export testing | `test_attendance_export.py` exists and exercises JSON, CSV, Excel, PDF, filtered, and professor export endpoints, but no saved result artifact from this script was found. `tools/api_test_report.md` lists attendance export endpoints as untested in the smoke report. | Script exists, but saved execution evidence was not found. |
| Deployment verification evidence | `docs/DEPLOYMENT_OPERATIONAL_DATASET_STATISTICS.md` documents inspected live deployment containers, PostgreSQL database, dataset folder, and API test artifacts. `DEPLOY_GODADDY.md` provides manual verification commands. | Deployment inspection evidence exists in documentation; raw command output logs are not committed. |

Tested endpoints evidenced by saved artifacts include:

- `GET /openapi.json`
- `POST /api/login`
- `GET /api/rooms`
- `GET /api/floors`
- `GET /api/courses`
- `GET /api/instructors`
- `GET /api/students`
- `GET /api/classes`
- `GET /api/room-schedule/{room_id}`
- `GET /api/debug/face-embedding-coverage-public`
- `GET /api/admin/users`
- `GET /api/admin/face-embedding-coverage`
- `GET /api/admin/system-settings`
- `GET /api/admin/analytics`
- `GET /api/admin/support/tickets`
- `POST /api/admin/users`
- `DELETE /api/admin/users/{user_id}`
- `POST /api/support/tickets`
- `PUT /api/admin/support/tickets/{ticket_id}`
- `POST /api/admin/support/tickets/{ticket_id}/replies`
- `POST /api/room-schedule/{room_code}`
- `DELETE /api/room-schedule/{room_code}`
- `POST /api/registration`
- `POST /api/capture`
- `POST /api/recognize`
- `GET /api/attendance` with valid parameters in the full-flow test result

## 3. Database Validation Evidence

| Validation item | Evidence currently available | Finding |
|---|---|---|
| Attendance insertion validation | Recognition inserts attendance into `attendance_logs` in `repositories/recognition_repo.py`. `tools/full_flow_attendance_test_results.json` shows the inserted attendance retrieved by API. `tests/test_e2e_attendance.py` asserts a matching row exists in `attendance_logs`. | Supported. |
| Enrollment validation | `repositories/registration_repo.py` inserts enrollments from registration schedule entries. `tests/test_e2e_attendance.py` registers a student with a course/section and then recognizes against the created class. | Supported by implementation and E2E test design. |
| Duplicate attendance detection | Recognition repository checks same student/class/date and applies `attendance_buffer_minutes`. | Implemented; direct saved duplicate test result not found. |
| Facial embedding storage | `services/face_embeddings.py` creates and upserts `student_face_embeddings`. `repositories/registration_repo.py` stores an embedding during registration, and `repositories/recognition_repo.py` updates the embedding cache after successful recognition. Local inspection found 54 rows in `student_face_embeddings`; deployment statistics report 56 stored embeddings. | Supported. |
| PostgreSQL migration verification | `scripts/migrate_sqlite_to_postgres.py` provides schema creation, data import, and identity reset. `scripts/compare_sqlite_postgres.py` compares SQLite and PostgreSQL table counts and primary-key differences. `docker-compose.prod.yml` defines a `migrate` profile using the migration script. No saved migration comparison output was found. | Migration tooling exists; saved comparison run output was not found. |
| SQLite to PostgreSQL consistency checks | `scripts/compare_sqlite_postgres.py` exists for table, row-count, and primary-key comparison. | Tooling exists; saved output not found. |
| Report generation validation | `test_attendance_export.py` exercises report export endpoints, but saved execution output was not found. | Test script exists; direct saved evidence not found. |
| Support ticket database operations | `tools/smoke_test_write_extended_results.json` records ticket creation, status update, and reply insertion with successful HTTP responses. Local database inspection found support ticket data, while deployment statistics report 22 support tickets. | Supported. |

Current local database measurements from `attendance.db`:

| Metric | Local value |
|---|---:|
| Students | 150 |
| Students with face data paths | 55 |
| Face embeddings | 54 |
| Enrollments | 53 |
| Attendance logs | 50 |
| Attendance logs with `Face recognized at` notes | 33 |
| Support tickets | 4 |

The live deployment statistics document reports higher production counts, including 150 students, 57 students with facial image paths, 56 stored embeddings, 265 attendance logs, 248 recognized attendance entries, and 22 support tickets.

## 4. Deployment Validation Evidence

| Deployment item | Evidence currently available | Finding |
|---|---|---|
| Successful container deployment | `docs/DEPLOYMENT_OPERATIONAL_DATASET_STATISTICS.md` identifies live containers `fras-backend-1`, `fras-frontend-1`, and `fras-db-1`. `docker-compose.prod.yml` defines those service roles. | Supported by deployment documentation and configuration. |
| Frontend/backend communication | `nginx/default.conf` proxies `/api/`, `/docs`, and `/openapi.json` to `backend:8000`. API smoke tests show OpenAPI and API endpoints responding. | Supported. |
| PostgreSQL container connectivity | `docker-compose.prod.yml` defines PostgreSQL 16, service health checks, backend dependency on healthy database, and `DATABASE_URL`. Deployment statistics identify PostgreSQL database `frasdb`. | Supported by config and deployment documentation. |
| Dataset bind mount usage | `docker-compose.prod.yml` mounts `./dataset:/app/dataset:rw`, and `repositories/registration_repo.py` uses `DATASET_PATH` for face images. Deployment statistics identify `/home/frasijbmapua/FRAS/dataset` and `/app/dataset`. | Supported. |
| Environment variable configuration | `.env.example`, `docker-compose.prod.yml`, `DEPLOY_GODADDY.md`, and `scripts/check_deployment_config.py` define or validate `JWT_SECRET`, `DATABASE_URL`, `DATASET_PATH`, `CORS_ORIGINS`, and PostgreSQL variables. | Supported. |
| Nginx reverse proxy functionality | `nginx/default.conf` contains proxy rules and SPA fallback. `DEPLOY_GODADDY.md` includes `curl` checks for `/docs` and assets. | Configured; raw production `curl` output is not committed. |
| Backend API accessibility | Smoke-test JSON reports show `/openapi.json`, `/test`, and multiple API endpoints returning successful responses. | Supported. |
| Production operational testing | Deployment statistics document summarizes live database, dataset, containers, and available test artifacts. | Supported by documentation; raw Docker log files are not committed. |

## 5. Recognition Workflow Operational Observations

Only observations directly supported by implementation or testing artifacts are listed here.

| Observation area | Supported observation |
|---|---|
| Recognition responsiveness | API scripts use request timeouts of 20 to 30 seconds for recognition and multipart upload flows. The system has configurable `recognition_timeout_seconds = 30`. No actual measured response-duration values were found. |
| Recognition delays | No saved duration metrics or latency measurements were found. |
| Image upload latency | Multipart upload flows were tested successfully for registration, capture, and recognition, but no upload-duration metric was recorded. |
| Embedding retrieval performance | The implementation limits recognition candidates to students enrolled in the selected class and loads stored embeddings from `student_face_embeddings`. This supports class-scoped embedding lookup, but no timing measurements were found. |
| Attendance logging speed | Recognition inserts attendance within the same API workflow and the full-flow result immediately retrieved the attendance row afterward. No measured insert duration was found. |
| Frontend response behavior | Documentation states the attendance monitor refreshes after recognition, and the backend returns structured JSON responses. Saved API artifacts show those response bodies, but no browser performance trace was found. |
| Environmental limitations | Deployment depends on correct `DATASET_PATH`, writable dataset mount, PostgreSQL environment variables, Nginx proxy routing, and sufficient runtime support for DeepFace/OpenCV. Deployment notes and config checks cover these requirements. |
| Classroom-scale usage observations | Deployment statistics show 20 distinct class-date attendance sessions and 248 recognized attendance entries in the live deployment summary. No concurrency/load-test or classroom crowd performance measurement was found. |

## 6. Evidence Gaps

The current repository and deployment documentation do not provide direct measurable evidence for the following:

- Persisted failed-recognition attempt history.
- Persisted recognition confidence, similarity, distance, or score values.
- Persisted recognition elapsed time, upload latency, or API response duration.
- A saved duplicate-attendance prevention test run.
- A saved schedule-validation failure test run.
- A saved proof that DeepFace fallback verification was triggered.
- A saved PostgreSQL migration comparison output from `scripts/compare_sqlite_postgres.py`.
- Saved report export execution output for CSV, Excel, and PDF.
- Raw production Docker, Nginx, or Uvicorn log files committed to the repository.

## 7. Summary

The repository contains meaningful operational validation evidence for successful and failed recognition API responses, multipart upload workflows, JWT login, role-based admin endpoint protection, attendance insertion, support-ticket writes, room schedule writes, Docker/Nginx/PostgreSQL deployment configuration, dataset mount usage, and production dataset counts. The strongest end-to-end evidence is `tools/full_flow_attendance_test_results.json`, which validates schedule creation, student registration, recognition success, and attendance retrieval in one workflow.

The main limitation is observability. Recognition attempts are not stored in a dedicated operational log table, and recognition timing, confidence, similarity, fallback usage, duplicate-block events, and schedule-failure events are not preserved as structured evidence. These behaviors are implemented in code, but only some are directly proven by saved test artifacts.
