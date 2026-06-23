# FRAS V2 Code Verification for Chapter 3

Inspection date: 2026-06-19  
Scope inspected: current FRAS repository code only. The thesis document was not edited.

Primary evidence files:

- Backend V2 API: `v2/api.py`
- Backend V2 service/business logic: `v2/service.py`
- Backend V2 repository/SQL access: `v2/repository.py`
- Backend V2 response/request models: `v2/models.py`
- Frontend routes: `facial-attendance/src/app/app.routes.ts`
- Frontend API client: `facial-attendance/src/app/api.service.ts`
- V2 frontend pages: `facial-attendance/src/app/v2/pages/**`
- V2 schema: `database/v2_schema.sql`
- V2 seed/verification scripts: `database/*v2*.py`
- Tests/scripts: `tests/**`, `tools/**`, root `test_*.py`

## 1. System Scope Actually Implemented

The implemented V2 workflow is primarily professor/instructor-facing. It includes login, class selection, live monitoring, manual and recognition-based attendance events, break handling, post-session review, evidence review, finalization, session history, and client-side CSV export. It does not implement a student-facing V2 portal workflow.

Implemented in V2 professor workflow:

| Feature | Status | Evidence |
|---|---:|---|
| Professor login | Implemented | `api/auth.py` exposes `POST /api/login`; `login.component.ts` routes non-admin users to `/v2/classes`. |
| Today's Classes | Implemented | `GET /api/v2/professors/{professor_id}/today/classes`; `todays-classes.component.ts`. |
| Class Roster / Student List | Implemented | `GET /api/v2/classes/{class_id}/students`; `class-roster.component.ts`. |
| Face Profile Registration / Update | Implemented | `GET/POST /api/v2/classes/{class_id}/students/{student_id}/face-profile`; `face-profile.component.ts`; `save_face_profile` in `v2/service.py`. |
| Live Session Monitoring | Implemented | `/live-session/:sessionId`; `GET /api/v2/sessions/{session_id}`; `live-session.component.ts`. |
| Manual Attendance | Implemented | `POST /api/v2/sessions/{session_id}/manual-attendance`; manual modal in live session and override mode in review/evidence pages. |
| Facial Recognition Capture | Implemented | `POST /api/v2/classes/{class_id}/recognize`; live-session webcam flow creates `time_in` or `break_in` events. |
| Session Break | Implemented | `POST /api/v2/sessions/{session_id}/break/start` and `/break/end`; `start_break`/`end_break`. |
| Return Detection Mode | Implemented | Live session auto capture is enabled in break mode; recognized students with last event `break_out` get `break_in`. |
| Post-Session Review | Implemented | `/session-review/:sessionId`; `GET /api/v2/sessions/{session_id}/review`. |
| Student Evidence | Implemented | `/student-evidence/:sessionId/:studentId`; loads review plus session events. |
| Mark Excused | Implemented through manual attendance override | Evidence page `markExcused()` and review override use `saveV2ManualAttendance(..., status='excused', lock_status=true)`. |
| Professor Override | Implemented through manual-attendance endpoint | `professor_overrides` insert occurs in `V2AttendanceRepository.apply_manual_status`. No separate `/override` endpoint exists. |
| Attendance Finalization | Implemented | `POST /api/v2/sessions/{session_id}/finalize`; `finalize_session` confirms records and marks session finalized. |
| Session History | Implemented | Professor-wide and class-specific endpoints plus history page. |
| Blackboard-ready CSV Export | Implemented client-side, not backend API | `post-session-review.component.ts` builds CSV after finalization. Columns are Student Number, Student Name, Attendance Status. |

Not part of the implemented V2 professor workflow:

| Feature | Status |
|---|---|
| Student portal | Not implemented in V2 route flow. |
| Student login | Legacy auth can map role `student` to `regular`, but no V2 student portal workflow is routed. |
| Full admin dashboard | Admin API/components exist in the repo, but active `app.routes.ts` does not define admin routes. Login attempts to route admins to `/admin/analytics`, which is not present in the current route table. Needs Verification if another Angular entrypoint is used. |
| Full user management workflow | Legacy/admin code exists (`api/admin.py`, `admin/user-management.component.ts`), but not in current V2 professor workflow routes. |
| Course management workflow | Legacy room/schedule/course APIs/components exist, but not in V2 professor workflow. |
| Support ticket workflow | Legacy support ticket API/components exist, but not in V2 professor workflow routes. |

## 2. Frontend Pages and Routes

| Page | Route | File path | Purpose | Main buttons/actions | Backend API calls used |
|---|---|---|---|---|---|
| Login | `/login` | `facial-attendance/src/app/login/login.component.ts` | Authenticates user and stores token/user metadata. | Login, show/hide password. | `POST /api/login`. |
| Today's Classes | `/v2/classes`, `/v2/today` redirect | `facial-attendance/src/app/v2/pages/todays-classes/todays-classes.component.ts` | Shows current/upcoming/completed classes for selected date. | Start Session, Resume Session, View History, Student List, date/professor selector. | `GET /api/v2/professors`, `GET /api/v2/professors/{id}/today/classes`, `GET /api/v2/professors/{id}/schedule`, `POST /api/v2/classes/{class_id}/sessions/start`. |
| Professor Schedule | `/v2/schedule` | Same component as Today's Classes | Shows assigned weekly schedule. | Start Monitor, History, Student List. | Same as Today's Classes. |
| Live Session | `/live-session/:sessionId` | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts` | Monitors attendance session, camera recognition, manual attendance, break mode. | Manual Capture, Auto Capture, Manual Attendance, Start Break, Unlock Break, End Break, End Session, quick override, bathroom break. | `GET /api/v2/sessions/{id}`, `GET /api/v2/professors/{id}/schedule`, `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{id}/events`, `POST /api/v2/sessions/{id}/manual-attendance`, `POST /api/v2/sessions/{id}/break/start`, `POST /api/v2/sessions/{id}/break/end`, `POST /api/v2/sessions/{id}/end`, `POST /api/login` for reauthentication. |
| Post-Session Review | `/session-review/:sessionId` | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` | Reviews computed attendance, warnings, overrides, and finalization. | View Details, Override Mode, Save Overrides, Finalize Attendance, Export Activity Logs, Export Review CSV, Export Blackboard CSV, Go to History. | `GET /api/v2/sessions/{id}/review`, `GET /api/v2/sessions/{id}`, `GET /api/v2/professors/{id}/schedule`, `POST /api/v2/sessions/{id}/manual-attendance`, `POST /api/v2/sessions/{id}/finalize`. |
| Student Evidence | `/student-evidence/:sessionId/:studentId` | `facial-attendance/src/app/v2/pages/student-evidence/student-evidence.component.ts` | Shows per-student timeline, presence ratio, assessment explanation, and override/confirmation controls. | Mark Excused, Override, Confirm Attendance, Back to Review. | `GET /api/v2/sessions/{id}/review`, `GET /api/v2/sessions/{id}`, `GET /api/v2/professors/{id}/schedule`, `POST /api/v2/sessions/{id}/manual-attendance`, `POST /api/v2/sessions/{id}/students/{student_id}/confirm`. |
| Class Session History | `/classes/:classId/session-history` | `facial-attendance/src/app/v2/pages/session-history/session-history.component.ts` | Shows historical sessions for one class. | Apply Filters, View Session Summary, Export Full History. | `GET /api/v2/classes/{class_id}/session-history`. |
| Professor Session History | `/session-history`, `/v2/history` redirect | Same Session History component | Shows all sessions for logged-in professor. | Apply Filters, View Session Summary, Export Full History. | `GET /api/v2/professors`, `GET /api/v2/professors/{id}/session-history`. |
| Class Roster | `/classes/:classId/students`, `/v2/classes/:classId/students` | `facial-attendance/src/app/v2/pages/class-roster/class-roster.component.ts` | Lists enrolled students, face profile status, recognition status, and attendance history preview. | Search, select student, Manage Face Data, Back to Classes. | `GET /api/v2/classes/{class_id}/students`. |
| Student Class History | `/classes/:classId/students/:studentId/history`, `/v2/classes/:classId/students/:studentId/history` | `facial-attendance/src/app/v2/pages/student-class-history/student-class-history.component.ts` | Shows one student's historical attendance for a class. | Filter, Clear Filters, View Session Evidence, Back to Roster. | `GET /api/v2/classes/{class_id}/students/{student_id}/history`. |
| Face Profile | `/classes/:classId/students/:studentId/face-profile`, `/v2/classes/:classId/students/:studentId/face-profile` | `facial-attendance/src/app/v2/pages/face-profile/face-profile.component.ts` | Captures and saves face profile images. | Start/stop camera, auto capture, manual capture, retake, reset, save profile. | `GET /api/v2/classes/{class_id}/students/{student_id}/face-profile`, `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile`. |

## 3. Backend API Endpoints

Authentication:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| POST | `/api/login` | Login and JWT issuance. | Login, break reauthentication. | `api/auth.py`; included by `backend.py`. |
| POST | `/login` | Backward-compatible login alias. | Not directly used by current V2 API service. | `api/auth.py`. |

Professor classes/schedule:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| GET | `/api/v2/professors` | List professor profiles. | Today's Classes, Session History. | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `professors`/`users`. |
| GET | `/api/v2/professors/{professor_id}/today/classes` | Current/upcoming/completed classes for date. | Today's Classes. | `list_professor_classes_for_day`, `classes`, `courses`, `rooms`, `enrollments`, `attendance_sessions`. |
| GET | `/api/v2/professors/{professor_id}/schedule` | Professor's assigned classes. | Today's Classes, Live Session, Review/Evidence. | `list_professor_schedule`. |

Class roster:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| GET | `/api/v2/classes/{class_id}/students` | Class roster with face/attendance summaries. | Class Roster. | `get_class_roster`, `list_class_roster_students`. |
| GET | `/api/v2/classes/{class_id}/students/{student_id}/history` | Per-student class history. | Student Class History. | `get_student_class_history`. |

Face profile:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| GET | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Face profile context/status. | Face Profile. | `get_face_profile_context`. |
| POST | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Saves active face profile and embeddings. | Face Profile. | `save_face_profile`, `replace_student_face_profile`, `student_face_profiles`, `student_face_embeddings`. |

Recognition:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| POST | `/api/v2/classes/{class_id}/recognize` | Recognizes uploaded frame against enrolled active embeddings. | Live Session. | `recognize_face_for_class`, `services/face_embeddings.py`, `student_face_profiles`, `student_face_embeddings`. |

Session lifecycle:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| POST | `/api/v2/classes/{class_id}/sessions/start` | Creates/reuses active session and initial student records. | Today's Classes. | `start_session`, `create_session`, `attendance_sessions`, `student_session_records`. |
| GET | `/api/v2/sessions/{session_id}` | Loads session, roster, event list. | Live Session, Student Evidence, Review export activity logs. | `get_session_detail`. |
| POST | `/api/v2/sessions/{session_id}/end` | Ends in-progress session and moves to review. | Live Session. | `end_session`, recalculation logic. |

Attendance events:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| POST | `/api/v2/sessions/{session_id}/events` | Creates `time_in`, `break_out`, `break_in`, `time_out`, manual/system event types. | Live Session. | `create_event`, `attendance_events`, `_recalculate_student_record`. |
| POST | `/api/v2/sessions/{session_id}/manual-attendance` | Saves manual attendance/override records. | Live Session, Post-Session Review, Student Evidence. | `save_manual_attendance`, `apply_manual_status`, `professor_overrides`. |

Break mode:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| POST | `/api/v2/sessions/{session_id}/break/start` | Sets session on break and creates `break_out` for present/late students with time-in. | Live Session. | `start_break`, `list_break_candidate_records`. |
| POST | `/api/v2/sessions/{session_id}/break/end` | Verifies professor password and resumes in-progress status. | Live Session. | `end_break`, `verify_user_password`. |

Post-session review / student evidence / finalization:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| GET | `/api/v2/sessions/{session_id}/review` | Loads summary and roster review state. | Post-Session Review, Student Evidence. | `get_session_review`, `_build_review_summary`. |
| POST | `/api/v2/sessions/{session_id}/finalize` | Recalculates records, confirms all, marks finalized. | Post-Session Review. | `finalize_session`, `confirm_session_records`. |
| POST | `/api/v2/sessions/{session_id}/students/{student_id}/confirm` | Confirms individual student record. | Student Evidence. | `confirm_student_record`. |

Export/session history:

| Method | URL | Purpose | Frontend | Backend files |
|---|---|---|---|---|
| GET | `/api/v2/professors/{professor_id}/session-history` | Professor-wide session history. | Session History. | `get_professor_session_history`. |
| GET | `/api/v2/classes/{class_id}/session-history` | Class session history. | Session History. | `get_class_session_history`. |
| None | V2 Blackboard CSV backend endpoint | Needs Verification / not found. CSV is generated client-side. | Post-Session Review. | `post-session-review.component.ts`; `blackboard_sync_logs` table exists but no V2 sync API was found. |

## 4. Database Tables / Models

Defined in `database/v2_schema.sql`:

| Table/model | Purpose | Important fields | Relationships |
|---|---|---|---|
| `users` | Authentication account table. | `user_id`, `email`, `password_hash`, `role`, `is_active`. | Linked to `professors.user_id`; `api/auth.py` maps role `professor` to frontend `instructor`. |
| `professors` | Professor profile and faculty metadata. | `professor_id`, `user_id`, `faculty_number`, names, `email`, units. | Referenced by `classes`, `attendance_sessions`, `professor_overrides`, `blackboard_sync_logs`. |
| `students` | Student profile records. | `student_id`, `student_number`, names, email, program, year level, `is_active`. | Referenced by `enrollments`, `student_face_profiles`, `student_session_records`, `attendance_events`. |
| `courses` | Course catalog. | `course_id`, `course_code`, `course_name`, `units`. | Referenced by `classes`. |
| `rooms` | Room/building data. | `room_id`, `room_number`, `floor_level`, `building`. | Referenced by `classes`. |
| `classes` | Scheduled class section handled by a professor. | `class_id`, `course_id`, `professor_id`, `room_id`, `section`, `day_of_week`, `start_time`, `end_time`, term/year, `is_active`. | Joins courses, professors, rooms; referenced by enrollments and attendance sessions. |
| `enrollments` | Student-to-class membership. | `enrollment_id`, `student_id`, `class_id`, `enrollment_status`. | Unique `(student_id, class_id)`. |
| `student_face_profiles` | Active face profile image/embedding metadata. | `face_profile_id`, `student_id`, `face_image_path`, `embedding_json`, `model_name`, `is_active`, timestamps. | One active profile per student enforced by partial unique index. |
| `attendance_status_types` | Seed list of status names. | `status_id`, `status_name`. | Lookup/seed table; current V2 records store status strings directly. |
| `attendance_sessions` | Per-class attendance session. | `session_id`, `class_id`, `professor_id`, scheduled/actual start/end, `session_status`, timer/break fields, `finalized_at`, `synced_to_blackboard`, `synced_at`. | Parent for student records, events, blackboard logs. |
| `student_session_records` | Per-student computed session state. | `record_id`, `session_id`, `student_id`, `final_status`, `system_assessment`, `time_in`, `time_out`, `total_presence_minutes`, `total_outside_minutes`, `break_count`, `late_minutes`, review/confirmation fields. | Unique `(session_id, student_id)`; referenced by attendance events and overrides. |
| `attendance_events` | Chronological evidence events. | `event_id`, `session_id`, `record_id`, `student_id`, `event_type`, `event_time`, `event_source`, `recognition_confidence`, `notes`, `is_voided`. | Drives recalculation. |
| `professor_overrides` | Audit trail for professor manual attendance and final overrides. | `override_id`, `record_id`, `professor_id`, `override_type`, previous/new status, reason, notes. | Written by `apply_manual_status`. |
| `blackboard_sync_logs` | Intended log for Blackboard sync/export. | `sync_id`, `session_id`, `sync_status`, `sync_message`, `synced_by_professor_id`, `synced_at`. | Table exists; no V2 API code found writing sync logs. Needs Verification for runtime use. |

Additional table used by face recognition:

- `student_face_embeddings` is created/used by `services/face_embeddings.py` and `database/seed_v2_face_profiles_from_images.py`. It is not defined in `database/v2_schema.sql`, but V2 service calls `ensure_embeddings_table()` before recognition/profile seeding.

Pydantic V2 models in `v2/models.py` define response/request objects such as `V2ClassCard`, `V2SessionResponse`, `V2StudentRecord`, `V2AttendanceEvent`, `V2ManualAttendanceRequest`, `V2SessionReviewResponse`, `V2ClassRosterResponse`, `V2FaceProfileSaveResponse`, and `V2RecognitionMatchResponse`.

## 5. Presence Monitoring Logic

Core calculation file/function:

- `v2/service.py`
- `V2AttendanceService._recalculate_student_record(session, record_id, student_id)`

Verified behavior:

| Item | Implementation |
|---|---|
| Time In | First event of type `time_in` or `manual_attendance` becomes `time_in`. Recognition creates `time_in` when recognized student has no `time_in`. |
| Break Out | Events of type `break_out` stop inside/presence timing, increment `break_count`, and start outside timing. Session break creates `break_out` for present/late students with `time_in`. |
| Break In | Events of type `break_in` stop outside timing and resume inside/presence timing. Return Detection Mode records `break_in` only if last event was `break_out`. |
| Time Out | Supported event type; stops inside timing and sets `time_out`. No obvious automatic frontend time-out creation was found. Needs Verification for live usage. |
| Manual Attendance | `manual_attendance` events count as time-in; manual status updates can mark present/late/absent/excused. |
| Professor Override | Implemented via `save_manual_attendance` with `lock_status=true`; records `professor_overrides` and sets `confirmed_by_professor`. |
| Presence Duration | Accumulated minutes between inside-starting events (`time_in`, `break_in`, `manual_attendance`) and outside/end events (`break_out`, `time_out`) or session end/current time. |
| Outside Duration | Accumulated minutes between `break_out` and next inside event or session end/current time. |
| Break Count | Incremented for each `break_out`. |
| Late calculation | `late_minutes = minutes_between(session_start, time_in)`. |
| System Assessment | `valid_presence` if ratio >= 0.8, `attendance_warning` if >= 0.6, otherwise `requires_review`; absent/no time-in handled separately. |
| Attendance Status | No time-in = absent. Late > 30 minutes = absent and requires review. Late > 15 minutes = late. Otherwise present if time-in exists; presence ratio may trigger warning/review. Professor-confirmed status overrides computed status. |

Important policy detail:

- The service uses the monitored session start (`actual_start` or `scheduled_start`) and session end (`actual_end` or current time).
- `final_status` can be `present`, `late`, `absent`, or `excused`. `partial` appears in some model/UI/test references but is not produced as a final status by `_recalculate_student_record`; reduced presence is represented through `system_assessment` warnings/review.

## 6. Manual Attendance and Facial Recognition Hybrid Workflow

The system supports both manual attendance and recognition-based events.

Manual attendance:

- Frontend:
  - Live Session modal saves all roster statuses through `saveV2ManualAttendance`.
  - Live Session quick override saves one selected student with `lock_status=true`.
  - Post-Session Review override mode saves changed statuses with `lock_status=true`.
  - Student Evidence Mark Excused/Override saves one status with `lock_status=true`.
- Backend:
  - `V2AttendanceService.save_manual_attendance` validates the session and records.
  - `V2AttendanceRepository.apply_manual_status` updates `student_session_records`, inserts into `professor_overrides`, and optionally confirms the record.
  - If status is `present` or `late` and no previous `time_in` exists, a `manual_attendance` event is created.

Facial recognition:

- Frontend:
  - Live Session captures webcam frames manually or every 5 seconds in auto mode.
  - Captured frame is uploaded to `POST /api/v2/classes/{class_id}/recognize`.
  - On a successful match, frontend creates an attendance event through `POST /api/v2/sessions/{session_id}/events`.
- Backend:
  - `recognize_face_for_class` extracts embeddings, loads enrolled active embeddings for the class, computes cosine similarity, and rejects below-threshold or ambiguous matches.
  - The recognition endpoint itself identifies the student; the separate session events endpoint records `time_in`/`break_in` and triggers recalculation.

## 7. Session Break and Return Detection

Implemented behavior:

- Starting break:
  - Frontend calls `POST /api/v2/sessions/{session_id}/break/start`.
  - Backend requires session status `in_progress`.
  - Backend sets `attendance_sessions.session_status = 'on_break'`.
  - Backend inserts `break_out` events for candidate records where final status is present/late and `time_in` is not null, skipping students whose last event is already `break_out`.
  - Backend recalculates each affected record.

- Return detection / `break_in`:
  - In break mode, live session starts auto capture and labels camera mode as Return Detection Mode.
  - Recognition only produces `break_in` during break if the recognized student's last event is `break_out`.
  - The frontend posts `break_in` through the same session events endpoint.

- Ending break:
  - Frontend first calls `POST /api/login` through `reauthenticate` to unlock controls.
  - Frontend then calls `POST /api/v2/sessions/{session_id}/break/end` with professor email and password.
  - Backend also verifies the password with `verify_user_password`.
  - Backend sets session status back to `in_progress`.

- Frontend lock/guard:
  - `SessionBreakGuard` stores `frasV2BreakSessionId` in localStorage and redirects navigation back to `/live-session/{id}` during active break.
  - `canDeactivate` prevents leaving the live session while `isBreakMode` is true.
  - Live Session blocks normal controls unless break is unlocked.

Needs Verification:

- There is no separate backend concept of a break interval table; break state is inferred from session status and events.
- No automatic timeout or penalty for exceeding individual break limit was found; the frontend displays a timer based on event notes.

## 8. Export Behavior

Verified exports:

- Post-Session Review has three client-side CSV downloads:
  - Review CSV: available when review data exists.
  - Activity Logs CSV: fetches `GET /api/v2/sessions/{session_id}` then exports event logs.
  - Blackboard CSV: enabled only when `session_status === 'finalized'`.
- Session History has a client-side full-history CSV export.

Blackboard CSV details:

- Trigger: `exportBlackboardCsv()` in `post-session-review.component.ts`.
- Requirement: `isFinalized` must be true; the button is disabled otherwise.
- Filename: `fras_blackboard_{course}_{section}_{date}_session-{sessionId}.csv`.
- Columns: `Student Number`, `Student Name`, `Attendance Status`.
- Status mapping:
  - `present` -> `Present`
  - `late` -> `Late`
  - `excused` -> `Excused`
  - anything else -> `Absent`

Direct Blackboard API integration:

- Not found in V2 code.
- `attendance_sessions` has `synced_to_blackboard` and `synced_at`.
- `blackboard_sync_logs` exists in schema.
- No V2 endpoint was found that writes sync logs or calls an external Blackboard API.

## 9. Seed Data and Test Accounts

Seed/init scripts found:

| File | Purpose |
|---|---|
| `database/init_v2_database.py` | Drops/recreates V2 PostgreSQL schema when run with `--force`. |
| `database/v2_schema.sql` | Defines V2 tables and indexes. |
| `database/seed_v2_from_v1.py` | Resets V2 from a V1 SQLite class snapshot; requires `--force`; creates one professor/class, students, enrollments, and face profiles from V1 embeddings if present. |
| `database/seed_v2_integration_data.py` | Imports faculty schedule data from DOCX, creates sample students, creates test professor, enrolls students. |
| `database/create_v2_test_professor.py` | Creates `test.professor@fras.local` with password `password123`, room `TEST-LAB`, and classes for all days/time slots. |
| `database/import_v2_professor_schedules.py` | Parses professor schedule DOCX and upserts professors/classes. |
| `database/seed_v2_face_profiles_from_images.py` | Seeds active face profiles and embeddings from `dataset/v2_face_profiles/{student_number}/active/front.*`. |
| `database/verify_v2_integration_seed.py` | Verifies seeded professor/test professor data. |
| `database/verify_v2_full_integration.py` | Exercises login, classes, roster, face context, session lifecycle, finalization, CSV shape, and recognition candidate. |
| `database/clear_v2_session_data.py` | Clears V2 sessions/records/events/overrides/sync logs when explicitly requested. |
| `database/clear_v2_face_data.py` | Clears V2 face data. |
| `database/check_v2_database.py`, `check_v2_seed.py`, `check_v2_roster_counts.py`, `audit_v2_face_data.py` | Database/seed/face data inspection scripts. |

Seeded data verified from scripts:

- Test professor account:
  - Email: `test.professor@fras.local`
  - Password: `password123`
  - Faculty number: `TEST-001`
  - Name: Testing Professor
  - Room: `TEST-LAB`
  - Classes: 7 days x 12 standard time slots = 84 classes, if script runs successfully.
- Faculty professor accounts:
  - Imported from DOCX by `import_v2_professor_schedules.py` through `seed_v2_integration_data.py`.
  - `verify_v2_full_integration.py` assumes real/faculty professor password `password`.
- Sample students:
  - `seed_v2_integration_data.py` defines 40 students with student numbers `2025103037` through `2025103074` plus several earlier numbers.
  - Program/year: BS Information Technology, 3rd Year.
- Courses/rooms/classes:
  - Courses are either imported from schedule data or seeded as `TEST101`, `TEST102`, `TEST103` if none exist for the test professor.
  - Rooms include imported rooms and `TEST-LAB`.
- Enrollments:
  - `seed_v2_integration_data.py` enrolls sample students into seeded faculty/test classes, excluding `ONLINE` rooms.
- Sample sessions/events:
  - `seed_v2_integration_data.py` does not appear to seed sample sessions/events.
  - `verify_v2_full_integration.py` creates sessions/events during verification.
  - `seed_v2_from_v1.py` truncates session/event tables and seeds class/student/profile data, not sample sessions.

Needs Verification:

- Actual current database contents were not modified. This report verifies seed scripts and schema, not live production row counts.

## 10. Testing Artifacts Actually Present

V2-specific or V2-adjacent tests/scripts:

| File path | Purpose | What it verifies | V1/V2/mixed |
|---|---|---|---|
| `tests/test_v2_api.py` | Pytest service/API smoke. | V2 routes registered, today classes, schedule, start session, create event, review, start break, end session. It appears stale because it calls `end_break(session_id)` without required payload. | V2, but likely needs update. |
| `tests/test_v2_recognition_decision.py` | Unit tests recognition decision rules. | Strong match, below threshold, ambiguous match, margin behavior. | V2. |
| `database/verify_v2_full_integration.py` | Scripted integration verification. | Login, schedule, roster, face context, student history, session exercise, finalization, history, evidence, statuses, Blackboard CSV shape, recognition candidate. | V2. |
| `database/verify_v2_integration_seed.py` | Seed verification. | Test/faculty login and seeded class/roster availability. | V2. |
| `tests/test_recognition_duplicate_attendance.py` | Unit test for duplicate attendance prevention. | Legacy recognition repository avoids duplicate same-day class attendance. | V1/legacy. |
| `tests/test_e2e_attendance.py` | End-to-end HTTP test using local server and SQLite DB. | Registration, recognition, attendance log creation, cleanup. | V1/legacy. |
| `tools/full_flow_attendance_test.py` | Scripted local HTTP flow. | Room/course schedule, registration, recognition, attendance fetch. | V1/legacy. |
| `tools/smoke_test_apis.py` and related `tools/smoke_test_*.py` | API smoke tests. | OpenAPI, login, public/admin endpoints, user/support/room schedule writes. | Mixed/mostly V1/admin. |
| `tools/api_test_report.md` | Summary of smoke-test run. | GET endpoints, admin auth, user/support/room schedule writes; notes export/file-upload endpoints not tested at that time. | Mixed/legacy. |
| Root `test_attendance_export.py` | Manual script for admin attendance export endpoint. | `/api/admin/attendance/export` JSON/CSV/Excel/PDF and professor export. | Admin/legacy, not V2 professor CSV. |
| Root `test_user_management.py`, `test_system_settings.py`, `test_support_ticket.py`, `test_super_admin_flow.py` | Admin/support tests. | User management, system settings, support tickets, super admin flow. | Admin/legacy. |
| Root `test_backend.py`, `test_backend_logic.py`, `test_flask_server.py`, `test_registration.py`, `test_query.py`, `test_server.py`, `test_import.py` | Older backend tests. | Various legacy/import/basic server behaviors. | V1/legacy/mixed. |

Existing V2 tests for requested items:

| Test target | Existing V2 evidence |
|---|---|
| login | Supported by `database/verify_v2_full_integration.py` and `verify_v2_integration_seed.py`; not a pytest V2 login test. |
| professor classes | `tests/test_v2_api.py`; `verify_v2_full_integration.py`. |
| class roster | `verify_v2_full_integration.py`; not in `tests/test_v2_api.py`. |
| start session | `tests/test_v2_api.py`; `verify_v2_full_integration.py`. |
| create event | `tests/test_v2_api.py`; `verify_v2_full_integration.py`. |
| start break | `tests/test_v2_api.py`. |
| break in | Needs Verification; no clear automated V2 `break_in` test found. |
| end session | `tests/test_v2_api.py`; `verify_v2_full_integration.py`. |
| review | `tests/test_v2_api.py`; `verify_v2_full_integration.py`. |
| finalize | `verify_v2_full_integration.py`; not obvious in `tests/test_v2_api.py`. |
| export | `verify_v2_full_integration.py` verifies CSV rows/filename shape; frontend client-side export not covered by browser E2E. |

## 11. What Testing Was Actually Supported by Code

Completed / Supported by Code:

- Happy path testing: supported through `tests/test_v2_api.py` and `database/verify_v2_full_integration.py`.
- API smoke testing: supported through `tools/smoke_test_*.py`, `tools/api_test_report.md`, and V2 route checks.
- Database seed verification: supported through `database/check_v2_*`, `verify_v2_integration_seed.py`, `verify_v2_full_integration.py`.
- Session lifecycle testing: supported for start session, create event, start break, end session, finalize in V2 service/script tests.
- Integration checks: supported by `database/verify_v2_full_integration.py`.

Needs Verification:

- Formal manual test case execution.
- Full frontend E2E testing of V2 pages in browser.
- Stress testing.
- Concurrency testing.
- Recognition accuracy benchmarking.
- False positive / false negative analysis.
- Confusion matrix evaluation.
- Automated test coverage for V2 break-in return detection.
- Automated test coverage for client-side CSV download behavior in Angular.

## 12. Chapter 3 Writing Notes

Research design:

- Describe the implemented system as a professor-facing classroom presence monitoring system.
- The system records attendance evidence through a hybrid method: manual professor input and facial-recognition-assisted event capture.
- Avoid claiming a student portal, student self-service workflow, or full admin/course/support management as part of the V2 professor workflow.

Development methodology:

- It is accurate to describe a prototype/iterative development approach using Angular/Ionic frontend, FastAPI backend, PostgreSQL V2 schema, and seed/verification scripts.
- Mention that the system separates API routing (`v2/api.py`), business logic (`v2/service.py`), database access (`v2/repository.py`), and data models (`v2/models.py`).
- Mention that legacy/admin modules remain in the repository but the V2 route flow centers on professor attendance monitoring.

Testing and evaluation:

- Code supports smoke, service-level, and integration-style verification for login, schedule/classes, roster, session lifecycle, manual overrides, finalization, CSV shape, and selected recognition logic.
- It is factual to say V2 integration scripts validate representative workflows and seed/database readiness.
- It is not supported by code evidence to claim completed formal user acceptance testing, stress testing, concurrency testing, or recognition accuracy benchmarking.

What not to claim:

- Do not claim direct Blackboard API integration. The implementation provides Blackboard-ready CSV export, generated client-side after finalization.
- Do not claim full student login/portal functionality for V2.
- Do not claim full admin dashboard/user/course/support management as part of V2 professor workflow, even though legacy/admin code exists.
- Do not claim confusion-matrix-level recognition evaluation unless separate evidence is produced.
- Do not claim break limit enforcement as a backend policy; current code displays/tags break limits but does not enforce an automatic timeout rule.
