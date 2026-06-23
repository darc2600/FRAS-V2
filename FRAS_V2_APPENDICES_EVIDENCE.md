# FRAS V2 Appendix Evidence Package

Prepared for the FRAS V2 thesis appendices. This document is based on repository inspection and one safe unit-test execution on 2026-06-23. It focuses on the implemented professor-centered V2 workflow and avoids unsupported claims. Sensitive configuration values are shown only as placeholders.

Primary evidence sources:

| Evidence type | Source |
|---|---|
| V2 schema | `database/v2_schema.sql`, `services/face_embeddings.py` |
| V2 API routes and response models | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| V2 business logic | `v2/service.py`, `v2/repository.py` |
| V2 frontend pages | `facial-attendance/src/app/v2/**`, `facial-attendance/src/app/app.routes.ts` |
| Session 3 evidence | `FRAS_V2_REPRESENTATIVE_FINALIZED_SESSION_CHAPTER_4_EVIDENCE.md` |
| Testing evidence | `tests/test_v2_recognition_decision.py`, `tests/test_v2_api.py`, `FRAS_V2_CHAPTER_4_TESTING_RESULTS.md` |
| Deployment evidence | `docker-compose.v2.yml`, `Dockerfile.backend.v2`, `facial-attendance/Dockerfile.v2`, `facial-attendance/nginx.v2.conf`, `.env.v2.example` |

## Appendix A: Database Schema and ERD Documentation

This appendix documents the V2 database entities used by the professor-centered classroom presence monitoring workflow. The V2 schema is centered on professor-owned classes, enrolled students, face profiles and embeddings, attendance sessions, event timelines, professor review actions, and Blackboard-ready export tracking. Older V1 and admin-heavy tables are excluded unless directly required by authentication or V2 recognition support.

### A.1 V2 Tables Used by the Final Workflow

| Table | Purpose in V2 workflow | Primary key | Important columns | Foreign keys / relationships | Evidence source |
|---|---|---|---|---|---|
| `users` | Stores login accounts used by professors and other roles. | `user_id` | `email`, `password_hash`, `role`, `is_active`, `created_at`, `updated_at` | One `users.user_id` may be linked to one `professors.user_id`. | `database/v2_schema.sql`, `api/auth.py` |
| `professors` | Stores professor identity used to scope Today's Classes, sessions, reviews, and exports. | `professor_id` | `user_id`, `faculty_number`, `first_name`, `last_name`, `email`, `total_units`, `lecture_units`, `lab_units` | `user_id` references `users(user_id)`; one professor has many `classes` and `attendance_sessions`. | `database/v2_schema.sql`, `v2/repository.py` |
| `students` | Stores student identity shown in rosters, session records, evidence pages, and CSV exports. | `student_id` | `student_number`, `first_name`, `last_name`, `email`, `program`, `year_level`, `is_active` | One student has many `enrollments`, `student_face_profiles`, `student_face_embeddings`, and `student_session_records`. | `database/v2_schema.sql` |
| `courses` | Stores course metadata displayed in Today's Classes, roster, review, and session history. | `course_id` | `course_code`, `course_name`, `units` | One course has many `classes`. | `database/v2_schema.sql` |
| `rooms` | Stores room labels for class context. | `room_id` | `room_number`, `floor_level`, `building` | One room may be assigned to many `classes`. | `database/v2_schema.sql` |
| `classes` | Stores scheduled class offerings owned by professors. | `class_id` | `course_id`, `professor_id`, `room_id`, `section`, `day_of_week`, `start_time`, `end_time`, `term`, `academic_year`, `is_active` | References `courses`, `professors`, and `rooms`; has many `enrollments` and `attendance_sessions`. | `database/v2_schema.sql`, `v2/repository.py` |
| `enrollments` | Links students to classes for roster loading and recognition candidate filtering. | `enrollment_id` | `student_id`, `class_id`, `enrollment_status` | References `students(student_id)` and `classes(class_id)`; unique pair `student_id, class_id`. | `database/v2_schema.sql` |
| `student_face_profiles` | Stores active face profile image path and metadata for student registration/update. | `face_profile_id` | `student_id`, `face_image_path`, `embedding_json`, `model_name`, `is_active`, `registered_at`, `updated_at` | References `students(student_id)`; unique active profile per student through partial index. | `database/v2_schema.sql`, `v2/service.py` |
| `student_face_embeddings` | Stores serialized recognition embeddings used by class-scoped facial recognition. | `embedding_id` | `student_id`, `model_name`, `embedding_json`, `source_image_path`, `created_at`, `updated_at` | Created by `services/face_embeddings.py`; joins to enrolled students during recognition. No explicit FK is declared in helper DDL. | `services/face_embeddings.py` |
| `attendance_status_types` | Normalizes basic attendance statuses. | `status_id` | `status_name` | Seeded with `present`, `late`, `absent`, `excused`. | `database/v2_schema.sql` |
| `attendance_sessions` | Stores one classroom monitoring session for a class/professor/date. | `session_id` | `class_id`, `professor_id`, `scheduled_start`, `scheduled_end`, `actual_start`, `actual_end`, `session_status`, `session_timer_seconds`, `is_long_break`, `long_break_minutes`, `finalized_at`, `synced_to_blackboard`, `synced_at` | References `classes(class_id)` and `professors(professor_id)`; parent of records, events, overrides, and sync logs. | `database/v2_schema.sql`, `v2/repository.py` |
| `student_session_records` | Stores per-student attendance assessment for one session. | `record_id` | `session_id`, `student_id`, `final_status`, `system_assessment`, `time_in`, `time_out`, `total_presence_minutes`, `total_outside_minutes`, `break_count`, `late_minutes`, `requires_review`, `review_reason`, `confirmed_by_professor`, `confirmed_at` | References `attendance_sessions` and `students`; unique pair `session_id, student_id`. | `database/v2_schema.sql` |
| `attendance_events` | Stores chronological evidence events such as time-in, breaks, return detection, manual attendance, and time-out. | `event_id` | `session_id`, `record_id`, `student_id`, `event_type`, `event_time`, `event_source`, `recognition_confidence`, `notes`, `is_voided`, `void_reason` | References `attendance_sessions`, optionally `student_session_records` and `students`. | `database/v2_schema.sql` |
| `professor_overrides` | Stores professor review/manual override evidence. | `override_id` | `record_id`, `professor_id`, `override_type`, `previous_status`, `new_status`, `reason`, `notes`, `created_at` | References `student_session_records` and `professors`. | `database/v2_schema.sql`, `v2/repository.py` |
| `blackboard_sync_logs` | Stores export/sync tracking metadata for finalized sessions. | `sync_id` | `session_id`, `sync_status`, `sync_message`, `synced_by_professor_id`, `synced_at`, `created_at` | References `attendance_sessions` and `professors`. Direct Blackboard API sync was not observed; frontend implements Blackboard-ready CSV download. | `database/v2_schema.sql`, `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` |

### A.2 Main ERD Relationships

| Relationship | Cardinality | Meaning |
|---|---|---|
| `users` to `professors` | 1 to 0..1 | A login account may be associated with one professor profile. |
| `professors` to `classes` | 1 to many | A professor owns scheduled classes. |
| `courses` to `classes` | 1 to many | A course may have multiple sections/classes. |
| `rooms` to `classes` | 1 to many | A room may host multiple scheduled classes. |
| `classes` to `enrollments` | 1 to many | Each class has enrolled students. |
| `students` to `enrollments` | 1 to many | A student may be enrolled in multiple classes. |
| `students` to `student_face_profiles` | 1 to many | A student may have historical profiles, with one active profile enforced by index. |
| `students` to `student_face_embeddings` | 1 to many | A student may have one embedding per model. |
| `classes` to `attendance_sessions` | 1 to many | A class may have multiple attendance sessions. |
| `attendance_sessions` to `student_session_records` | 1 to many | A session creates one record per enrolled student. |
| `student_session_records` to `attendance_events` | 1 to many | A student record may have multiple timeline events. |
| `student_session_records` to `professor_overrides` | 1 to many | A professor may create override evidence for a student record. |
| `attendance_sessions` to `blackboard_sync_logs` | 1 to many | A finalized session may have export/sync log records. |

### A.3 ERD Capture Recommendation

For the appendix, manually capture a schema diagram or generated ERD showing only the tables above. Recommended screenshot/output:

| Screenshot / output | How to capture |
|---|---|
| V2 ERD diagram | Use the table list in A.1 in a database ERD tool, or convert `FRAS_V2_MERMAID_DIAGRAMS_FOR_THESIS.md` into an image if it contains the desired V2 ERD. |
| PostgreSQL table list | From the running deployment, capture `\dt` or an equivalent database admin view filtered to the V2 workflow tables. |
| Table columns | Capture `\d attendance_sessions`, `\d student_session_records`, `\d attendance_events`, and `\d professor_overrides` if required by the panel. |

## Appendix B: V2 API Documentation

This appendix documents the implemented V2 API endpoints used by the final professor-centered workflow. V2 routes are registered under `/api/v2` in `v2/api.py`; authentication still uses the existing login endpoint from `api/auth.py` and frontend `AuthService`.

### B.1 Authentication Endpoint

| Method | Endpoint | Purpose | Request | Response / notes | Evidence source |
|---|---|---|---|---|---|
| POST | `/api/login` | Authenticates the professor and returns login/session data used by the frontend guard. | JSON with `email` and `password`. | Response shape is implemented in the existing auth module; do not include real credentials in the appendix. | `api/auth.py`, `facial-attendance/src/app/auth.service.ts`, `facial-attendance/src/app/login/login.component.ts` |

Sample request:

```json
{
  "email": "professor@example.edu",
  "password": "<PASSWORD>"
}
```

### B.2 Professor, Class, Roster, and History Endpoints

| Method | Endpoint | Purpose | Request body / parameters | Sample response fields | Evidence source |
|---|---|---|---|---|---|
| GET | `/api/v2/professors` | Lists professor summaries. | None. | `professor_id`, `user_id`, `faculty_number`, `professor_name`, `email`, unit counts. | `v2/api.py`, `v2/models.py` |
| GET | `/api/v2/professors/{professor_id}/today/classes` | Loads Today's Classes grouped into current, upcoming, and completed. | Path: `professor_id`; optional query: `target_date=YYYY-MM-DD`. | `professor_id`, `date`, `current[]`, `upcoming[]`, `completed[]`. | `v2/api.py`, `facial-attendance/src/app/v2/pages/todays-classes` |
| GET | `/api/v2/professors/{professor_id}/schedule` | Loads all active professor classes for schedule view. | Path: `professor_id`. | `classes[]` with class, course, room, day, time, and student count. | `v2/api.py` |
| GET | `/api/v2/classes/{class_id}/students` | Loads class roster, face profile status, recognition status, and attendance summary. | Path: `class_id`. | `class_context`, `students[]`. | `v2/api.py`, `facial-attendance/src/app/v2/pages/class-roster` |
| GET | `/api/v2/classes/{class_id}/students/{student_id}/history` | Loads one student's class attendance history. | Path: `class_id`, `student_id`. | `header`, `summary`, `records[]`. | `v2/api.py`, `facial-attendance/src/app/v2/pages/student-class-history` |
| GET | `/api/v2/professors/{professor_id}/session-history` | Loads professor-wide session history. | Path: `professor_id`. | `summary`, `sessions[]`. | `v2/api.py`, `facial-attendance/src/app/v2/pages/session-history` |
| GET | `/api/v2/classes/{class_id}/session-history` | Loads session history for one class. | Path: `class_id`. | `class_context`, `summary`, `sessions[]`. | `v2/api.py`, `v2/models.py` |

Sample Today's Classes response shape:

```json
{
  "professor_id": 5,
  "date": "2026-06-17",
  "current": [
    {
      "class_id": 50,
      "course_code": "ITS131P",
      "course_name": "Pending Course Name - ITS131P",
      "section": "BM10",
      "room": "TBA",
      "day_of_week": "Wednesday",
      "start_time": "10:30:00",
      "end_time": "14:00:00",
      "student_count": 40,
      "status": "current",
      "active_session_id": 3
    }
  ],
  "upcoming": [],
  "completed": []
}
```

### B.3 Face Profile and Recognition Endpoints

| Method | Endpoint | Purpose | Request body / parameters | Sample response fields | Evidence source |
|---|---|---|---|---|---|
| GET | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Loads context for registering or updating a student face profile. | Path: `class_id`, `student_id`. | Student identity, class context, `face_profile_status`, `last_face_update`. | `v2/api.py`, `v2/models.py` |
| POST | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Saves uploaded face profile images and embeddings. | `multipart/form-data`: `angles[]`, `images[]`. | `status`, `message`, `student_id`, `face_profile_status`, `saved_angles`, `image_paths`. | `v2/api.py`, `v2/service.py` |
| POST | `/api/v2/classes/{class_id}/recognize` | Runs class-scoped recognition against active enrolled embeddings. | `multipart/form-data`: `image`. | `status`, `student_id`, `student_name`, `confidence`, `decision_result`, `best_match_score`, thresholds and matched IDs. | `v2/api.py`, `services/face_embeddings.py` |

### B.4 Live Session, Events, Break, Review, and Finalization Endpoints

| Method | Endpoint | Purpose | Request body / parameters | Sample response fields | Evidence source |
|---|---|---|---|---|---|
| POST | `/api/v2/classes/{class_id}/sessions/start` | Starts a live attendance session and creates student session records. | JSON: `professor_id`, optional `session_date`. | `session`, `roster`, `events`. | `v2/api.py`, `tests/test_v2_api.py` |
| GET | `/api/v2/sessions/{session_id}` | Loads live session detail including roster and events. | Path: `session_id`. | `session`, `roster`, `events`. | `v2/api.py` |
| POST | `/api/v2/sessions/{session_id}/events` | Creates timeline events for time-in, break-out, break-in, time-out, capture failures, and related evidence. | JSON: `student_id`, `event_type`, `event_source`, optional `event_time`, `recognition_confidence`, `notes`. | Updated `session`, `roster`, `events`. | `v2/api.py`, `v2/models.py` |
| POST | `/api/v2/sessions/{session_id}/manual-attendance` | Saves manual attendance, professor overrides, and Mark Excused status. | JSON: `professor_id`, `records[]`, `notes`, `lock_status`. | Updated session detail. | `v2/api.py`, `v2/repository.py` |
| POST | `/api/v2/sessions/{session_id}/break/start` | Starts a session-wide break and enables return detection workflow. | Empty JSON object. | Updated session detail with break events. | `v2/api.py`, `facial-attendance/src/app/v2/pages/live-session` |
| POST | `/api/v2/sessions/{session_id}/break/end` | Ends session break after professor reauthentication. | JSON: `professor_email`, `password`. | Updated session detail. | `v2/api.py`, `api.auth.verify_user_password` |
| POST | `/api/v2/sessions/{session_id}/end` | Ends live monitoring and moves session to post-session review. | Empty JSON object. | `session`, `summary`, `roster`. | `v2/api.py` |
| GET | `/api/v2/sessions/{session_id}/review` | Loads post-session review summary and student records. | Path: `session_id`. | `summary` counts and `roster`. | `v2/api.py`, `facial-attendance/src/app/v2/pages/post-session-review` |
| POST | `/api/v2/sessions/{session_id}/students/{student_id}/confirm` | Confirms one student record during professor review. | Path: `session_id`, `student_id`. | Updated review response. | `v2/api.py` |
| POST | `/api/v2/sessions/{session_id}/finalize` | Finalizes attendance and enables CSV export. | Empty JSON object. | Final review response with `session_status` finalized. | `v2/api.py`, `post-session-review.component.ts` |

Sample manual attendance request:

```json
{
  "professor_id": 5,
  "records": [
    { "record_id": 101, "student_id": 39, "status": "excused" }
  ],
  "notes": "Approved excuse after professor review.",
  "lock_status": true
}
```

### B.5 Blackboard-Ready CSV Export

| Feature | Implementation | Evidence source | Verification status |
|---|---|---|---|
| Blackboard-ready CSV download | Implemented in frontend after finalization through `exportBlackboardCsv()`. Header: `Student Number`, `Student Name`, `Attendance Status`. Filename pattern: `fras_blackboard_{course}_{section}_{date}_session-{sessionId}.csv`. | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` | Verified by code inspection. |
| Direct Blackboard API sync | Not observed in the V2 implementation. `blackboard_sync_logs` exists in schema, but the inspected workflow supports CSV download rather than direct LMS API submission. | `database/v2_schema.sql`, frontend review component | Not available / not verified. |

### B.6 API Screenshots to Capture

| Screenshot / output | Suggested capture |
|---|---|
| Swagger/OpenAPI route list | Open `/docs` in the running system and capture the `/api/v2` section. |
| Today's Classes JSON | Use Swagger or browser dev tools to capture `GET /api/v2/professors/{professor_id}/today/classes`. |
| Session Review JSON | Capture `GET /api/v2/sessions/3/review` if the deployed database still contains Session 3. |
| CSV file | Finalized session review page, click Blackboard CSV export, then capture the downloaded CSV opened in Excel/Word. |

## Appendix C: Testing and Operational Validation Evidence

This appendix summarizes available tests, executed test results, and operational validation scripts. The repository contains both safe unit tests and scripts that reset, seed, or write session data. Only the recognition decision unit test was executed during this appendix preparation.

### C.1 Executed Test Evidence

| Test file | Purpose | Command executed | Result | Notes |
|---|---|---|---|---|
| `tests/test_v2_recognition_decision.py` | Validates V2 recognition decision rules: strong unique match, below-threshold match, ambiguous top matches, and margin behavior. | `.\.venv\Scripts\python.exe -m pytest tests\test_v2_recognition_decision.py -q` | Passed: `5 passed in 13.32s` | Safe unit test; no database reset, seed, or write observed. |

### C.2 Inspected but Not Executed Because They Can Reset, Seed, or Write Data

| File | Purpose | Why not executed for appendix preparation | Evidence |
|---|---|---|---|
| `tests/test_v2_api.py` | Tests route registration, Today's Classes, schedule, start session, event creation, review, break start/end, and session end. | `setup_module()` calls `init_v2_database(["--force"])` and `seed_v2_database([])`, which can reset and seed the database. | File inspection. |
| `database/verify_v2_full_integration.py` | Full V2 integration flow including session creation, events, override, finalization, CSV filename/content, and recognition attempt. | It writes session data and finalizes sessions. | Existing evidence in `FRAS_V2_CHAPTER_4_TESTING_RESULTS.md`. |
| `database/clear_v2_session_data.py` | Clears V2 sessions, records, events, overrides, and CSV logs. | Destructive cleanup script. | File name and `rg` inspection. |
| `database/clear_v2_face_data.py` | Clears V2 face profiles/embeddings. | Destructive cleanup script. | File name and `rg` inspection. |
| `scripts/reset_demo_data.py` | Rebuilds/reset demo data and embeddings. | Writes and resets data. | File name and code references. |

### C.3 Operational Verification Scripts and Observed Limitations

| File | Purpose | Status in available evidence | Limitation |
|---|---|---|---|
| `database/verify_v2_integration_seed.py` | Verifies DB identity, row counts, professor login, Today's Classes, schedule, and roster. | Previously attempted; failed locally because host `db` was not resolvable from the shell. | Requires running inside Docker network or using a reachable `DATABASE_URL`. |
| `database/check_v2_database.py` | Lists public database tables. | Previously attempted; failed locally because host `db` was not resolvable. | Same Docker hostname limitation. |
| `database/check_v2_seed.py` | Checks seed data and class records. | Previously attempted; failed locally because host `db` was not resolvable. | Same Docker hostname limitation. |
| `database/check_v2_roster_counts.py` | Checks V2 roster counts and duplicate/sample enrollments. | Previously attempted; failed locally because host `db` was not resolvable. | Same Docker hostname limitation. |
| `database/audit_v2_face_data.py` | Audits face profiles and embeddings. | Previously attempted; failed locally because host `db` was not resolvable. | Same Docker hostname limitation. |

### C.4 Test Coverage by Workflow Step

| Workflow step | Evidence status | Source |
|---|---|---|
| Login | Supported by implementation; not unit-tested in executed run. | `api/auth.py`, `facial-attendance/src/app/login`, `auth.service.ts` |
| Today's Classes | Supported by implementation and inspected integration test. | `v2/api.py`, `tests/test_v2_api.py` |
| Class Roster | Supported by implementation. | `v2/api.py`, `class-roster.component.ts` |
| Face Profile Registration/Update | Supported by implementation. | `v2/api.py`, `face-profile.component.ts`, `services/face_embeddings.py` |
| Live Session Monitoring | Supported by implementation and inspected integration test. | `live-session.component.ts`, `v2/service.py` |
| Manual Attendance / Professor Override / Mark Excused | Supported by implementation. | `manual-attendance` endpoint, `v2/repository.py`, `post-session-review.component.ts` |
| Facial Recognition Capture | Recognition decision unit tests executed; full DeepFace/live camera accuracy not benchmarked. | `tests/test_v2_recognition_decision.py`, `services/face_embeddings.py` |
| Session Break / Return Detection | Supported by implementation and inspected integration test. | `break/start`, `break/end`, `live-session.component.ts` |
| Post-Session Review / Student Evidence | Supported by implementation. | `post-session-review.component.ts`, `student-evidence.component.ts` |
| Finalization / Session History / CSV Export | Supported by implementation; CSV is browser-side. | `finalize` endpoint, `session-history.component.ts`, `post-session-review.component.ts` |

### C.5 Not Verified or Not Available

| Item | Status |
|---|---|
| Formal biometric accuracy metrics | Not available in repository evidence. |
| False positive / false negative rates | Not available in repository evidence. |
| Confusion matrix | Not available in repository evidence. |
| Stress or concurrency testing | Not available in repository evidence. |
| Formal usability study | Not available in repository evidence. |
| Direct Blackboard API integration test | Not available; CSV export is implemented. |

## Appendix D: Representative Session Evidence

This appendix summarizes the representative finalized session evidence used for Chapter IV. The available evidence file states that the session was inspected from a deployed PostgreSQL database and that a session-boundary correction was applied after backup. The evidence should be presented as Session 3 evidence, not as a database-wide performance or accuracy claim.

### D.1 Session 3 Context

| Field | Value |
|---|---|
| Evidence source | `FRAS_V2_REPRESENTATIVE_FINALIZED_SESSION_CHAPTER_4_EVIDENCE.md` |
| Session ID | `3` |
| Class ID | `50` |
| Course code | `ITS131P` |
| Course name | `Pending Course Name - ITS131P` |
| Section | `BM10` |
| Professor | Polycarpio Cabalag Ii |
| Scheduled start | `2026-06-17T10:30:00` |
| Scheduled end | `2026-06-17T14:00:00` |
| Actual start | `2026-06-17T12:01:13.494843` |
| Actual end | `2026-06-17T13:11:38.485791` |
| Session status | `finalized` |
| Enrolled students | 40 |
| Student session records | 40 |
| Attendance events | 161 |
| Professor-confirmed records | 40 |
| Professor overrides linked to session records | 40 |

### D.2 Final Status Distribution

| Final status | Count |
|---|---:|
| Present | 40 |
| Late | 0 |
| Absent | 0 |
| Excused | 0 |
| Other | 0 |

### D.3 System Assessment Distribution

| System assessment | Count |
|---|---:|
| `valid_presence` | 40 |
| `attendance_warning` | 0 |
| `requires_review` | 0 |
| `absent` | 0 |
| Other | 0 |

### D.4 Attendance Event Distribution

| Event type | Count |
|---|---:|
| `time_in` | 38 |
| `break_out` | 41 |
| `break_in` | 40 |
| `time_out` | 40 |
| `manual_attendance` | 2 |
| `professor_override` | 0 |
| Other | 0 |

### D.5 Event Source Distribution

| Event source | Count |
|---|---:|
| `facial_recognition` | 57 |
| `manual_professor` | 25 |
| `system` | 79 |
| Other | 0 |

### D.6 Presence Monitoring Metrics

| Metric | Count |
|---|---:|
| Students with `total_presence_minutes > 0` | 40 |
| Students with `total_outside_minutes > 0` | 40 |
| Students with `break_count > 0` | 40 |
| Students with `late_minutes > 0` | 40 |

Important limitation: the evidence file notes that some duration values should be described as stored system values unless independently validated.

### D.7 Coleman, Matthew Sample Student Timeline

| Field | Value |
|---|---|
| Student number | `2025103039` |
| Student name | Coleman, Matthew |
| Final status | `present` |
| System assessment | `valid_presence` |
| Time in | `2026-06-17T12:41:49.324442` |
| Time out | `2026-06-17T13:11:38.485791` |
| Total presence minutes | 6 |
| Total outside minutes | 53 |
| Break count | 2 |
| Late minutes | 40 |
| Confirmed by professor | true |

Chronological attendance events:

| Timestamp | Event type | Source | Notes |
|---|---|---|---|
| `2026-06-17T12:11:15.490121` | `break_out` | `manual_professor` | Bathroom Break Out. Limit: 10 minutes. |
| `2026-06-17T12:41:49.324442` | `manual_attendance` | `manual_professor` | Saved from V2 live session manual attendance modal. |
| `2026-06-17T12:42:01.192551` | `break_out` | `system` | Session Break started by professor. Return Detection Mode enabled. |
| `2026-06-17T13:05:35.216709` | `break_in` | `facial_recognition` | Auto Capture recognized Coleman, Matthew. |
| `2026-06-17T13:11:38.485791` | `time_out` | `system` | Reconstructed session end boundary. Student automatically timed out 30 seconds after the last original attendance event. |

### D.8 Screenshots to Capture for Session 3

| Screenshot / output | Suggested capture |
|---|---|
| Today's Classes showing the class card | Professor dashboard / Today's Classes page. |
| Live Session Monitoring | Session 3 live session screen if reproducible from session history or demo state. |
| Post-Session Review summary | Session 3 review page showing counts and finalized status. |
| Student Evidence for Coleman, Matthew | Student evidence page showing chronological events. |
| Blackboard-ready CSV | Downloaded CSV for Session 3. |
| Database read-only query output | Optional: query output showing Session 3 counts and distributions. |

## Appendix E: Deployment and Environment Configuration

This appendix summarizes the V2 deployment and environment configuration observed in the repository. The V2 stack uses Docker Compose with PostgreSQL, FastAPI/Uvicorn, Angular/Ionic served by Nginx, and a mounted dataset directory for face images.

### E.1 Runtime Components

| Component | Technology / file | Purpose |
|---|---|---|
| Backend API | FastAPI served by Uvicorn; `Dockerfile.backend.v2`; command `uvicorn backend:app --host 0.0.0.0 --port 8000` | Provides authentication, V2 attendance workflow, face profile, recognition, session review, and finalization endpoints. |
| Frontend | Angular/Ionic; `facial-attendance/Dockerfile.v2`; `facial-attendance/nginx.v2.conf` | Provides professor-facing V2 pages. |
| Database | PostgreSQL 16 Alpine in `docker-compose.v2.yml` | Stores V2 schema and attendance/session records. |
| Reverse proxy / static serving | Nginx in frontend container | Serves compiled frontend and proxies API requests as configured. |
| Face recognition | DeepFace and OpenCV-related libraries | Extracts embeddings from uploaded face images and recognition captures. |
| Dataset storage | `DATASET_PATH`, default `/app/dataset`; volume `./dataset:/app/dataset:rw` | Stores face profile images and dataset files. |

### E.2 Environment Variables

| Variable | Purpose | Safe example |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username. | `<POSTGRES_USER>` |
| `POSTGRES_PASSWORD` | PostgreSQL password. | `<POSTGRES_PASSWORD>` |
| `POSTGRES_DB` | PostgreSQL database name. | `fras_v2` |
| `POSTGRES_PORT` | Host port mapped to PostgreSQL. | `5432` |
| `JWT_SECRET` | JWT signing secret. | `<JWT_SECRET>` |
| `JWT_EXPIRE_MINUTES` | JWT expiry duration. | `1440` |
| `DATABASE_URL` | Backend DB connection string. | `postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/fras_v2` |
| `FRAS_MODE` | Enables V2 mode. | `v2` |
| `DATASET_PATH` | Dataset mount path used by backend. | `/app/dataset` |
| `CORS_ORIGINS` | Allowed browser origins. | `http://localhost:8080,http://127.0.0.1:8080` |
| `BACKEND_PORT` | Host port for backend. | `8000` |
| `FRONTEND_PORT` | Host port for frontend. | `8080` |
| `FRAS_V2_FACE_SIMILARITY_THRESHOLD` | Optional V2 recognition similarity threshold. | `0.70` |
| `FRAS_V2_FACE_MATCH_MARGIN` | Optional top-match margin for ambiguity detection. | `0.07` |

### E.3 Deployment Verification Steps

| Step | Command or action | Expected evidence |
|---|---|---|
| Build/start V2 stack | `docker compose -f docker-compose.v2.yml up -d --build` | `db`, `backend`, and `frontend` containers running. |
| Check backend health | `curl -fsS http://localhost:8000/docs` | FastAPI Swagger UI responds. |
| Check frontend | Open `http://localhost:8080` | Login or V2 Classes page loads. |
| Check database health | `docker compose -f docker-compose.v2.yml ps` | `db` marked healthy. |
| Check V2 routes | Open `/docs` and inspect `/api/v2` endpoints. | V2 Attendance group visible. |
| Verify dataset mount | Inspect container path `/app/dataset` or upload a face profile. | Face profile image files appear under dataset path. |
| Verify no secrets in screenshots | Redact `.env`, connection strings, tokens, and passwords. | Screenshots show only placeholder or non-sensitive values. |

### E.4 Sensitive Data Handling

Do not include real `.env` values, database passwords, JWT secrets, SSH credentials, access tokens, private keys, or personally confidential credentials in the thesis appendix. Use placeholders such as `<POSTGRES_PASSWORD>`, `<JWT_SECRET>`, and `<PROFESSOR_EMAIL>`.

## Appendix F: System Implementation Documentation

This appendix describes the main implemented modules for the V2 professor-centered workflow. The descriptions focus on files used by the final workflow rather than older V1/admin-heavy functionality.

### F.1 Backend Implementation Modules

| File path | Role in V2 implementation | Workflow coverage |
|---|---|---|
| `backend.py` | FastAPI application setup, CORS middleware, router inclusion, and V2-only mode handling through `FRAS_MODE`. | Application entry point. |
| `v2/api.py` | Defines `/api/v2` routes for professors, classes, face profiles, recognition, sessions, events, break mode, review, confirmation, and finalization. | Main V2 API contract. |
| `v2/models.py` | Pydantic request and response models for V2 API. | Typed API payloads. |
| `v2/service.py` | Business logic for Today's Classes, session lifecycle, face profile save, recognition decisions, break workflow, review summaries, overrides, and finalization. | Professor-centered workflow logic. |
| `v2/repository.py` | SQL data-access layer for V2 tables. | Database reads/writes for classes, sessions, records, events, overrides, and history. |
| `services/face_embeddings.py` | Creates embedding table, extracts embeddings with DeepFace, stores/loads embeddings, computes cosine similarity, and parses embedding JSON. | Face profile and recognition support. |
| `services/db.py` | Provides database connection wrapper for PostgreSQL or SQLite fallback. | Database connectivity. |
| `database/v2_schema.sql` | Fresh PostgreSQL V2 schema. | ERD/schema foundation. |

Representative backend route snippet:

```python
router = APIRouter(prefix="/api/v2", tags=["V2 Attendance"])

@router.get("/professors/{professor_id}/today/classes", response_model=V2TodayClassesResponse)
def get_today_classes(professor_id: int, target_date: date | None = Query(default=None), service: V2AttendanceService = Depends(get_v2_attendance_service)):
    return service.get_today_classes(professor_id=professor_id, target_date=target_date)

@router.post("/sessions/{session_id}/manual-attendance", response_model=V2SessionDetailResponse)
def save_manual_attendance(session_id: int, payload: V2ManualAttendanceRequest, service: V2AttendanceService = Depends(get_v2_attendance_service)):
    return service.save_manual_attendance(session_id=session_id, payload=payload)
```

Representative recognition decision configuration:

```python
V2_MIN_RECOGNITION_SIMILARITY = float(os.getenv("FRAS_V2_FACE_SIMILARITY_THRESHOLD", "0.70"))
V2_RECOGNITION_MARGIN = float(os.getenv("FRAS_V2_FACE_MATCH_MARGIN", "0.07"))
```

### F.2 Frontend Implementation Modules

| File path | Role in V2 implementation | Workflow coverage |
|---|---|---|
| `facial-attendance/src/app/app.routes.ts` | Defines V2 professor routes and guards. | Navigation and route protection. |
| `facial-attendance/src/app/api.service.ts` | Central Angular service for V2 HTTP calls. | Frontend-to-backend API integration. |
| `facial-attendance/src/app/v2/models/v2-attendance.models.ts` | TypeScript interfaces matching V2 API models. | Typed frontend data contract. |
| `facial-attendance/src/app/v2/pages/todays-classes/*` | Today's Classes and schedule page. | Professor class dashboard. |
| `facial-attendance/src/app/v2/pages/class-roster/*` | Class roster with face profile and attendance status. | Roster and face profile entry point. |
| `facial-attendance/src/app/v2/pages/face-profile/*` | Face profile registration/update page. | Student face profile workflow. |
| `facial-attendance/src/app/v2/pages/live-session/*` | Live session monitoring, capture, manual attendance, specific student breaks, session break, and return detection workflow. | Live classroom monitoring. |
| `facial-attendance/src/app/v2/pages/post-session-review/*` | Post-session review, professor overrides, finalization, activity log export, Blackboard-ready CSV export. | Review and final output. |
| `facial-attendance/src/app/v2/pages/student-evidence/*` | Student-level session evidence view. | Individual student timeline evidence. |
| `facial-attendance/src/app/v2/pages/session-history/*` | Professor/class session history. | Historical review. |
| `facial-attendance/src/app/v2/components/*` | Shared V2 UI components such as cards, tables, status badges, timeline, topbar, and sidebar. | Reusable V2 UI presentation. |

Representative frontend API service snippet:

```typescript
getV2TodayClasses(professorId: number, targetDate?: string): Observable<V2TodayClassesResponse> {
  let url = `${this.backendUrl}/api/v2/professors/${professorId}/today/classes`;
  if (targetDate) {
    url += `?target_date=${encodeURIComponent(targetDate)}`;
  }
  return this.http.get<V2TodayClassesResponse>(url);
}

recognizeV2Face(classId: number, image: File): Observable<V2RecognitionMatchResponse> {
  const formData = new FormData();
  formData.append('image', image);
  return this.http.post<V2RecognitionMatchResponse>(`${this.backendUrl}/api/v2/classes/${classId}/recognize`, formData);
}
```

Representative Blackboard-ready CSV implementation:

```typescript
private blackboardFilename(): string {
  return `fras_blackboard_${this.classFilenamePart()}_${this.sessionDatePart()}_session-${this.sessionId}.csv`;
}

private buildCsvRows(blackboardOnly: boolean): string[][] {
  const header = blackboardOnly
    ? ['Student Number', 'Student Name', 'Attendance Status']
    : ['Student Number', 'Student Name', 'Status', 'Presence Minutes', 'Outside Minutes', 'Break Count', 'System Assessment', 'Review Reason'];
  // Rows are built from the finalized roster.
  return [header, ...rows];
}
```

### F.3 Manual Screenshots and Outputs to Add to Word

| Appendix section | Recommended screenshot/output |
|---|---|
| Database schema | ERD diagram; selected table definitions for session tables. |
| API documentation | Swagger `/docs` with `/api/v2` expanded; one sample JSON response. |
| Testing | Terminal screenshot of `5 passed in 13.32s` for `tests/test_v2_recognition_decision.py`. |
| Representative session | Session 3 review summary; Coleman, Matthew evidence timeline; downloaded CSV file. |
| Deployment | Docker Compose service status; frontend login/classes page; backend `/docs`; Nginx or container health check. |
| Implementation | Screenshots of key files or IDE tree showing `v2/` backend and `src/app/v2/` frontend modules. |

### F.4 Unsupported Claims to Avoid

| Claim | Reason to avoid |
|---|---|
| "The system proves biometric accuracy." | No formal accuracy benchmark, false-positive rate, false-negative rate, or confusion matrix was verified. |
| "The system directly syncs with Blackboard through an API." | The inspected V2 implementation supports Blackboard-ready CSV export; direct API sync was not observed. |
| "All integration tests were executed." | Some integration tests reset, seed, or write database state and were intentionally not executed. |
| "Session 3 duration metrics are independently validated." | Evidence file notes duration values should be treated as stored system values unless independently validated. |
| "The local shell verified live PostgreSQL." | Prior evidence shows Docker hostname `db` was not resolvable locally; live DB verification should be run inside Docker/networked deployment. |
