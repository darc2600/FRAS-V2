# FRAS V2 System Documentation

> Source-of-truth summary of the implemented FRAS V2 system (codebase-derived).

---

## 1. System Overview

FRAS V2 is a Classroom Presence Monitoring system that evolved from the original facial-recognition attendance project. The implemented V2 system focuses on capturing and evaluating student presence across monitored sessions using facial recognition embeddings and a session-based event model. It is designed for professor-driven workflows where the instructor starts and manages live sessions and finalizes attendance for export.

Key monitored concepts implemented in the codebase:

- Time In
- Time Out
- Break Out
- Break In
- Presence Duration
- Outside Duration
- Session Review
- Student Evidence
- Attendance Finalization
- CSV Export (Blackboard-compatible export generated during review/finalize flows)

## 2. Technology Stack

- Frontend framework: Angular (source under `facial-attendance/src/` — Ionic/Angular components present)
- Backend framework: FastAPI (v2 endpoints under `v2/` and additional FastAPI routes in `backend.py`)
- Database: PostgreSQL for V2 schema (`database/v2_schema.sql`) — legacy code also supports SQLite (local dev)
- Facial recognition / embeddings: DeepFace is used for embedding extraction (see `services/face_embeddings.py`) and custom similarity logic
- Deployment/runtime: Uvicorn served FastAPI app (startup helper `start_server.py`). The repo includes scripts for initializing a Postgres V2 schema (`database/init_v2_database.py`).

## 3. User Roles and Scope

Implemented user role in V2:

- Professor / Instructor (professors table, professor-specific APIs and flows)

Explicitly NOT implemented in V2 (per codebase and routes):

- Student portal / Student login (no student-facing authenticated portal implemented)
- Student login (students are seeded/used but no student dashboard)
- Admin dashboard (admin APIs exist in `api/admin.py` but a full admin UI is not part of V2 front-end pages)
- Full user management workflow (limited registration / user creation helper endpoints exist)
- Course management workflow (course/class seed + import utilities exist, but no full CMS UI)
- Faculty records workflow (faculty import utilities are provided, but not a full HR flow)

## 4. Implemented Frontend Pages

Frontend sources (Angular) live under `facial-attendance/src/app/` and routes are defined in [facial-attendance/src/app/app.routes.ts](facial-attendance/src/app/app.routes.ts).

Implemented V2 pages (from routes & modules):

- Login
  - Route: `/login`
  - Purpose: Authenticate professor users (calls `POST /api/login`)
  - Main displayed data: Email/password form
  - Actions: Submit credentials to receive JWT
  - Backend API calls: `POST /api/login` (alias `/api/login` and `/login` handled by `api/auth.py`)

- Today’s Classes
  - Route: `/v2/classes` (also `/v2/today`, `/v2/schedule`)
  - Purpose: Show professor's classes for the selected date with Current / Upcoming / Completed grouping
  - Main displayed data: class cards (course code, section, room, time, status)
  - Main actions/buttons: Start Session (when applicable), navigate to Session History or Class Roster
  - Backend API calls: `GET /api/v2/professors/{professor_id}/today/classes` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/todays-classes](facial-attendance/src/app/v2/pages/todays-classes)

- Class Roster / Student List
  - Route: `/v2/classes/:classId/students` (and `classes/:classId/students`)
  - Purpose: Show enrolled students, face profile status, recognition status, recent attendance summaries
  - Main displayed data: roster rows with student name/number, status, last face update, recognition confidence, attendance rate
  - Actions: Navigate to face-profile or student history, open student evidence
  - Backend API calls: `GET /api/v2/classes/{class_id}/students` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/class-roster](facial-attendance/src/app/v2/pages/class-roster)

- Face Profile Registration / Update
  - Route: `/v2/classes/:classId/students/:studentId/face-profile`
  - Purpose: Upload multiple angle images to register/update a student's face profile
  - Main displayed data: existing profile status, last update, previews of captured images
  - Actions: Upload images with angles (requires "front" image), Save profile
  - Backend API calls: `GET /api/v2/classes/{class_id}/students/{student_id}/face-profile`, `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/face-profile](facial-attendance/src/app/v2/pages/face-profile)

- Student Attendance History (per student)
  - Route: `/v2/classes/:classId/students/:studentId/history`
  - Purpose: Show a student's session-by-session attendance records and durations
  - Main displayed data: rows of sessions (date, scheduled start/end, presence/outside minutes, break count, system assessment)
  - Actions: Export or review individual session rows
  - Backend API calls: `GET /api/v2/classes/{class_id}/students/{student_id}/history` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/student-class-history](facial-attendance/src/app/v2/pages/student-class-history)

- Live Session / Monitor Page
  - Route: `/live-session/:sessionId` (page uses live session state)
  - Purpose: Monitor recognition, auto-capture, manual capture, and send attendance events during a live session
  - Main displayed data: session roster summary, recent recognition activity, action log
  - Main actions/buttons: Switch Auto/Manual capture, Manual capture button, Start Break, End Break (unlock with professor password), End Session
  - Backend API calls used: `POST /api/v2/classes/{class_id}/sessions/start`, `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{session_id}/events`, `POST /api/v2/sessions/{session_id}/break/start`, `POST /api/v2/sessions/{session_id}/break/end`, `POST /api/v2/sessions/{session_id}/end` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/live-session](facial-attendance/src/app/v2/pages/live-session)

- Post-Session Review
  - Route: `/session-review` (and review routes under `/session-history`)
  - Purpose: Review roster, warnings, manual overrides, mark excused/override statuses, finalize attendance
  - Main displayed data: review summary (present/late/partial/absent/excused), roster with requires_review flags and review reasons
  - Actions: Override student status, Mark Excused, Confirm record, Finalize Attendance, Export Blackboard CSV
  - Backend API calls: `GET /api/v2/sessions/{session_id}/review`, `POST /api/v2/sessions/{session_id}/finalize`, `POST /api/v2/sessions/{session_id}/students/{student_id}/confirm`, `POST /api/v2/sessions/{session_id}/manual-attendance` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/post-session-review](facial-attendance/src/app/v2/pages/post-session-review)

- Student Evidence / Session Detail
  - Route: `/student-evidence` (and module paths)
  - Purpose: Inspect a student's recognition timeline and captured evidence for a specific session; allow professor to confirm/override
  - Main displayed data: student record timeline, events, images, recognition confidence, notes
  - Actions: Confirm attendance, Override status, Mark Excused
  - Backend API calls: `GET /api/v2/sessions/{session_id}` (session detail includes roster and events), `POST /api/v2/sessions/{session_id}/events`, `POST /api/v2/sessions/{session_id}/students/{student_id}/confirm`
  - Frontend source: [facial-attendance/src/app/v2/pages/student-evidence](facial-attendance/src/app/v2/pages/student-evidence)

- Session History
  - Route: `/session-history` (also `/v2/history` redirect)
  - Purpose: List past sessions for a class or professor, summary statistics and CSV export
  - Main displayed data: rows for sessions with attendance rate, average presence minutes, warning counts
  - Actions: Download CSV, navigate to session review/evidence
  - Backend API calls: `GET /api/v2/professors/{professor_id}/session-history`, `GET /api/v2/classes/{class_id}/session-history` ([v2/api.py](v2/api.py))
  - Frontend source: [facial-attendance/src/app/v2/pages/session-history](facial-attendance/src/app/v2/pages/session-history)

- Settings (limited)
  - Route: Settings components exist in `facial-attendance` UI; backend settings service implemented under `services/settings_service.py`.
  - Purpose: System & recognition thresholds (UI presence may be partial).

## 5. Full Professor Workflow (Implemented)

High-level flow implemented end-to-end in code:

1. Login
   - Professor authenticates via `POST /api/login` (see `api/auth.py`). Token returned is used by frontend.
   - Data recorded: none in V2 beyond optional last-login placeholder.

2. Today’s Classes
   - Professor opens `/v2/classes` which calls `GET /api/v2/professors/{professor_id}/today/classes` ([v2/api.py](v2/api.py)).
   - System retrieves scheduled classes from `classes`, `courses`, `rooms`, and active session (if any).

3. Student List / Class Roster
   - Navigate to class roster: `GET /api/v2/classes/{class_id}/students`.
   - System returns roster summary including face profile status and recognition metrics. No DB write occurs on read.

4. Register or Update Face Profile
   - Professor captures multiple angle images via UI and POSTs to `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile`.
   - System stores images under `DATASET_PATH` (default `dataset/v2_face_profiles/...`). It also extracts embeddings with DeepFace (`services/face_embeddings.py`) and upserts embeddings into `student_face_embeddings` table (or embedding store), and inserts an active row into `student_face_profiles`.
   - Files touched: `services/face_embeddings.py`, repository method `replace_student_face_profile` ([v2/repository.py](v2/repository.py)).

5. Start Live Session
   - Professor clicks Start Session; frontend calls `POST /api/v2/classes/{class_id}/sessions/start` with payload `V2StartSessionRequest` including `professor_id`.
   - Backend: repository creates `attendance_sessions` row (status `in_progress`) and inserts `student_session_records` rows for active enrollments ([v2/repository.py#create_session]).

6. Auto Capture / Manual Capture
   - The live UI captures frames and calls `POST /api/v2/classes/{class_id}/recognize` to obtain a possible match (embedding extraction uses DeepFace server-side in `V2AttendanceService.recognize_face_for_class`).
   - If a confident match is found and conditions allow, the frontend triggers `POST /api/v2/sessions/{session_id}/events` with an event type (e.g., `time_in`, `manual_attendance`, `manual_capture`) to record evidence.
   - Events are stored in `attendance_events` and triggers recalculation of the student's `student_session_records` computed fields (presence/outside/break counts) via `_recalculate_student_record` in `v2/service.py`.

7. Session Break / Return Detection Mode
   - Professor clicks Start Break -> `POST /api/v2/sessions/{session_id}/break/start`. The server:
     - Changes `attendance_sessions.session_status` to `on_break` (via `V2AttendanceRepository.set_session_status`).
     - Creates `break_out` events for students who are currently marked present/late (see `start_break` in `v2/service.py`).
     - Frontend will restrict manual attendance during break and switch auto-capture to only accept `break_in` facial-recognition returns.
   - End Break requires professor password verification: `POST /api/v2/sessions/{session_id}/break/end` with `V2BreakUnlockRequest` verified by `verify_user_password` in `api/auth.py`.
   - Implemented behavior: start break, create `break_out` events, lock manual attendance; return detection accepts only `break_in` from `facial_recognition` while `session_status == 'on_break'`.

8. End Session
   - Professor ends session: `POST /api/v2/sessions/{session_id}/end`.
   - Backend sets `actual_end`, changes session_status to `under_review`, and recalculates each student's record.

9. Post-Session Review
   - Professor opens session review: `GET /api/v2/sessions/{session_id}/review` returns session, roster, and review summary (system assessment and flags).
   - Professor may apply manual attendance adjustments via `POST /api/v2/sessions/{session_id}/manual-attendance` which writes `professor_overrides` and may create `manual_attendance` events.

10. Student Evidence
   - Clicking an individual student shows timeline from `GET /api/v2/sessions/{session_id}` and the roster + event list. Professor can confirm record (`POST /api/v2/sessions/{session_id}/students/{student_id}/confirm`) or create override events.

11. Finalize Attendance
   - Professor finalizes: `POST /api/v2/sessions/{session_id}/finalize`.
   - Backend marks session `finalized`, calls `confirm_session_records`, and sets `finalized_at`. Once finalized, the session is locked from changes and CSV export becomes available.

12. Export CSV
   - Frontend triggers Blackboard CSV generation and download from frontend code (CSV generation logic is performed in utilities/tests and in `database/verify_v2_full_integration.py` for expected format). CSV filename generation and content follows Blackboard-style rows (see verify script).

13. Session History
   - Professor navigates to `GET /api/v2/professors/{professor_id}/session-history` or `GET /api/v2/classes/{class_id}/session-history` to see past sessions and summary statistics.

## 6. Attendance Event Lifecycle

Implemented attendance event types (enforced in `v2/models.V2CreateEventRequest`):

- `time_in` — Student arrived / detected inside
- `break_out` — Student left the monitored area for break
- `break_in` — Student returned from break
- `time_out` — Student left session at end
- `manual_attendance` — Created when professor marks attendance via manual input
- `manual_capture`, `false_recognition`, `missed_recognition`, `camera_failure`, `network_failure` — other event categories supported

How events contribute to records (implemented in `_recalculate_student_record` in `v2/service.py`):

- Presence duration: computed by summing intervals between inside-start and outside events bounded by session end
- Outside duration: intervals when student was out (between `break_out` and `break_in`)
- Break count: incremented for each `break_out` event
- Attendance status: final_status computed from presence ratio vs monitored minutes and late thresholds (logic in `_recalculate_student_record`)
- System assessment: one of `valid_presence`, `attendance_warning`, `requires_review`, or `absent` depending on duration/ratio and late arrival

Professor confirmation overrides final_status and sets `system_assessment` to `valid_presence` for confirmed present/late/excused.

## 7. Session Break / Return Detection Mode

Implemented behavior (code):

- When professor clicks Session Break (`POST /api/v2/sessions/{session_id}/break/start`):
  - `attendance_sessions.session_status` set to `on_break` (`V2AttendanceRepository.set_session_status`).
  - For all current present/late records, system creates `break_out` events and recalculates records.
  - While `session_status == 'on_break'`, `V2AttendanceService.create_event` restricts incoming events: it allows only `break_in` with `event_source == 'facial_recognition'` (server returns 423 Locked for other event types).
  - End Break (`POST /api/v2/sessions/{session_id}/break/end`) requires professor password verification (`verify_user_password`) — the endpoint exists and is enforced in `v2/service.py`.

Implemented vs Pending:
- Implemented: status transition to `on_break`; `break_out` event creation; `break_in` return detection enforcement; lock on manual attendance while on break.
- Needs Verification: frontend UI lock/protection details across all components — code indicates `SessionBreakGuard` and checks in components, but exact UX locks require running the app to confirm.

## 8. Database Schema / Data Model

The V2 relational schema is defined in `database/v2_schema.sql` (Postgres). Key tables and purpose/fields:

- `users` — authentication records for system users (email, password_hash, role)
- `professors` — professor metadata (professor_id, user_id, faculty_number, name, email, units)
- `students` — student metadata (`student_id`, `student_number`, name, email, program)
- `courses` — courses (`course_id`, `course_code`, `course_name`)
- `rooms` — rooms (`room_id`, `room_number`)
- `classes` — scheduled classes linking course + professor + room + day + time
- `enrollments` — student enrollments in classes
- `student_face_profiles` — uploaded face images and metadata (face_image_path, embedding_json, model_name, is_active)
- `attendance_sessions` — live session records (scheduled_start/end, actual_start/end, session_status, finalized_at)
- `student_session_records` — per-session per-student aggregated record (final_status, time_in/time_out, total_presence_minutes, total_outside_minutes, break_count, late_minutes, requires_review, confirmed flags)
- `attendance_events` — raw event logs (event_type, event_time, event_source, recognition_confidence)
- `professor_overrides` — history of professor manual/override actions
- `blackboard_sync_logs` — logs for export/sync to LMS (Blackboard) if used

References:
- Schema file: [database/v2_schema.sql](database/v2_schema.sql)
- Repository code that manipulates these tables: [v2/repository.py](v2/repository.py)

## 9. Backend API Endpoints

Primary V2 API (defined in [v2/api.py](v2/api.py), prefix `/api/v2`):

Authentication (legacy / shared):
- `POST /api/login` — login and return JWT token (`api/auth.py`)

Professor classes and schedule:
- `GET /api/v2/professors` — list professors
- `GET /api/v2/professors/{professor_id}/today/classes` — today's classes for professor
- `GET /api/v2/professors/{professor_id}/schedule` — professor schedule
- `GET /api/v2/professors/{professor_id}/session-history` — professor session history

Class roster and student context:
- `GET /api/v2/classes/{class_id}/students` — class roster
- `GET /api/v2/classes/{class_id}/students/{student_id}/history` — student class history
- `GET /api/v2/classes/{class_id}/students/{student_id}/face-profile` — face profile context
- `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile` — save face profile (multipart form images)

Recognition & capture:
- `POST /api/v2/classes/{class_id}/recognize` — upload image to recognize face against enrolled embeddings for the class

Session lifecycle & events:
- `POST /api/v2/classes/{class_id}/sessions/start` — start a session
- `GET /api/v2/sessions/{session_id}` — get session detail (roster + events)
- `POST /api/v2/sessions/{session_id}/events` — create attendance event (time_in, break_out, break_in, time_out, manual_attendance, ...)
- `POST /api/v2/sessions/{session_id}/manual-attendance` — apply manual attendance records from professor
- `POST /api/v2/sessions/{session_id}/break/start` — start break (system creates break_out events)
- `POST /api/v2/sessions/{session_id}/break/end` — end break (requires professor password)
- `POST /api/v2/sessions/{session_id}/end` — end session and move to under_review
- `GET /api/v2/sessions/{session_id}/review` — session review summary
- `POST /api/v2/sessions/{session_id}/finalize` — finalize attendance (locks and enables export)
- `POST /api/v2/sessions/{session_id}/students/{student_id}/confirm` — professor confirms a student record

Other legacy/utility endpoints (non-exhaustive):
- `POST /api/capture` — capture endpoint for raw image capture (`api/capture.py`)
- `GET /api/attendance` — legacy attendance retrieval (`api/attendance.py`)
- Additional v1 endpoints exist under `api/` (e.g., `recognition.py`, `registration.py`, `schedule.py`, `course_students.py`) used by older frontend paths; V2 frontend uses `/api/v2` routes.

See implementations: [v2/api.py](v2/api.py), [backend.py](backend.py) (includes legacy endpoints and dynamic router inclusion), and per-route service implementations in `v2/service.py` and `v2/repository.py`.

## 10. Seed Data and Test Accounts

Seed utilities and test data exist under `database/`:

- `database/create_v2_test_professor.py` — creates a test professor account:
  - Email: `test.professor@fras.local`
  - Password: `password123` (development-only default printed by script)
  - Faculty number: `TEST-001`
  - Script also seeds courses, rooms, and many test classes. See [database/create_v2_test_professor.py](database/create_v2_test_professor.py)

- `database/seed_v2_integration_data.py` — seeds sample students, enrollments, optionally imports faculty DOCX schedules, and enrolls students into classes. The script prints the test professor credentials and counts.

- `database/seed_v2_from_v1.py` and other migration helpers exist to migrate legacy data into V2 schema.

Notes: these scripts expect `DATABASE_URL` environment variable and will seed PostgreSQL V2 schema. For quick local testing some scripts use SQLite fallbacks.

## 11. CSV Export

- Export is handled client-side by the Angular frontend using data returned from `GET /api/v2/sessions/{session_id}/review` (finalized session). The Post-Session Review UI offers an "Export Blackboard CSV" button (see [post-session-review component](facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts)).
- Export requirements: frontend expects session to be `finalized` before enabling Blackboard CSV export.
- Output format/columns: CSV rows generated by frontend utilities follow Blackboard formatting used in integration verification scripts (see `database/verify_v2_full_integration.py` which constructs `_csv_rows` and `_blackboard_filename`).

## 12. QA and Integration Readiness

What is covered in repo tests and smoke checks:
- Unit/integration tests: `tests/test_v2_api.py`, recognition tests (`tests/test_recognition_duplicate_attendance.py`), end-to-end attendance flow (`tests/test_e2e_attendance.py`) — indicates API flows are exercised by test suite.
- Database smoke / seed verification scripts: `database/check_v2_seed.py`, `database/verify_v2_full_integration.py` and related helpers exist.
- Backend startup: `start_server.py` launches FastAPI app with Uvicorn and includes the V2 router.

Needs Verification:
- Frontend build status: `fras_index.html` indicates a built web app is present, while full-source Angular app exists under `facial-attendance/src/`. Confirm that `npm` build scripts and `package.json` (top-level) are current for building the frontend.
- Deployment: repository includes Dockerfile(s) and `docker-compose.*` variants, but your deployment configuration/environment variables (DATABASE_URL, JWT_SECRET) must be verified in target environment.

## 13. Known Limitations

- Facial recognition quality depends on DeepFace model and environmental conditions (lighting, occlusions). This is noted in code and test comments.
- Auto pose validation: the face-profile upload requires a `front` image but multi-angle automation (5-angle automatic capture) is implemented in UI only to the extent the capture component supports multiple angle uploads; enforcement happens server-side (front required).
- Student-facing functionality: there is no student portal or student login implemented in V2.
- Some legacy endpoints and SQLite compatibility remain; running V2 in production expects a Postgres `DATABASE_URL` and to initialize `database/v2_schema.sql`.
- Security: password hashing depends on installed libraries (`passlib` / `bcrypt`). If missing, plaintext fallback exists — ensure production uses proper hashing.

## 14. Thesis Paper Notes

How to map this documentation to thesis sections:

- Chapter 1 (Problem & Objectives): Use the System Overview and Problem Statement. Cite the V2 goals: automated presence validation, break detection, and professor-driven finalization.
- Chapter 3 (System Design): Include architecture diagram references: frontend (Angular) -> backend FastAPI -> Postgres; services layer (`v2/service.py`, `services/face_embeddings.py`), repository layer (`v2/repository.py`), and DB schema (`database/v2_schema.sql`).
- Chapter 4 (Implementation): Provide implementation details referencing:
  - `v2/api.py` (endpoint definitions)
  - `v2/service.py` (session lifecycle, event handling, presence calculation)
  - `v2/repository.py` (SQL queries and DB mappings)
  - `services/face_embeddings.py` (DeepFace usage)
  - Frontend pages: `facial-attendance/src/app/v2/...` for UI flows and components
- Chapter 5 (Testing & Evaluation): Reference `tests/test_v2_api.py`, `database/verify_v2_full_integration.py`, and `tests/test_e2e_attendance.py` for automated checks and integration scenarios.
- Appendices: Add screenshots from the built frontend (`fras_index.html` / built bundles), sample seed data (from `database/seed_v2_integration_data.py`), DB schema (`database/v2_schema.sql`) and example CSVs from the integration script.

Caveats & verification notes (mark uncertain items):
- "Frontend build status" and exact steps to produce the production `fras_index.html` bundle should be verified locally (`facial-attendance` project's `npm`/`ionic` build). — Needs Verification
- Any deployed environment-specific settings (e.g., S3 usage, Blackboard integration webhooks) require checking environment variables and deployment scripts — Needs Verification

---

Files referenced in this document (quick links):
- [v2/api.py](v2/api.py)
- [v2/service.py](v2/service.py)
- [v2/repository.py](v2/repository.py)
- [v2/models.py](v2/models.py)
- [database/v2_schema.sql](database/v2_schema.sql)
- [database/seed_v2_integration_data.py](database/seed_v2_integration_data.py)
- [database/create_v2_test_professor.py](database/create_v2_test_professor.py)
- [services/face_embeddings.py](services/face_embeddings.py)
- [facial-attendance/src/app/app.routes.ts](facial-attendance/src/app/app.routes.ts)
- [facial-attendance/src/app/v2/pages](facial-attendance/src/app/v2/pages)
- [backend.py](backend.py)
- [start_server.py](start_server.py)

If you want, I can:
- Run the frontend build (needs `npm`/`ionic` installed) and verify the built `fras_index.html` bundle.
- Generate a short appendix with the full list of API endpoints (including example request/response shapes) extracted from Pydantic models.

