# FRAS V2 Live Database Results for Chapter 4

Generated from read-only live database inspection on 2026-06-19. No reset, seed, truncate, insert, update, delete, or new session creation was performed.

## 1. Database Connection Context

- Command run from: deployed Docker backend container via SSH and `docker compose -f docker-compose.prod.yml exec -T backend`.
- Connection result: Connected to PostgreSQL successfully.
- Database name: `fras_v2`.
- Database user: `fras_v2`.
- PostgreSQL server address from container: `172.18.0.2/32`.
- PostgreSQL server port: `5432`.
- Read-only confirmation: the inspection explicitly ran `BEGIN READ ONLY`; `SHOW transaction_read_only` returned `on`.
- Note: `SHOW default_transaction_read_only` returned `off`, meaning the database is not globally read-only, but this inspection transaction was read-only.

## 2. Live V2 Database Counts

| Table | Count |
|---|---:|
| users | 16 |
| professors | 16 |
| students | 40 |
| courses | 36 |
| rooms | 37 |
| classes | 255 |
| enrollments | 9,480 |
| student_face_profiles | 47 |
| student_face_embeddings | 40 |
| attendance_sessions | 5 |
| student_session_records | 200 |
| attendance_events | 172 |
| professor_overrides | 40 |
| blackboard_sync_logs | 0 |

## 3. Session Status Counts

| Session status | Count |
|---|---:|
| finalized | 2 |
| in_progress | 2 |
| under_review | 1 |

No sessions with `on_break`, `ended`, or other statuses were found in the live database during inspection.

## 4. Attendance Event Counts

### By Event Type

| Event type | Count |
|---|---:|
| time_in | 74 |
| break_out | 50 |
| break_in | 46 |
| manual_attendance | 2 |

No `time_out` events or `professor_override` events were found in `attendance_events` during inspection.

### By Event Source

| Event source | Count |
|---|---:|
| facial_recognition | 97 |
| manual_professor | 30 |
| system | 45 |

No `manual`, `professor_override`, or other event_source values were found. The live database uses `manual_professor` rather than plain `manual`.

## 5. Student Session Record Counts

### By Final Status

| Final status | Count |
|---|---:|
| absent | 124 |
| present | 76 |

### By System Assessment

| System assessment | Count |
|---|---:|
| absent | 124 |
| attendance_warning | 9 |
| requires_review | 24 |
| valid_presence | 43 |

### By Professor Confirmation

| confirmed_by_professor | Count |
|---|---:|
| false | 80 |
| true | 120 |

### Record Metrics

| Metric | Count |
|---|---:|
| records with total_presence_minutes > 0 | 70 |
| records with total_outside_minutes > 0 | 43 |
| records with break_count > 0 | 43 |
| records with late_minutes > 0 | 73 |

## 6. Representative Finalized or Under-Review Session

A finalized session was found and selected.

| Field | Value |
|---|---|
| session_id | 4 |
| class_id | 201 |
| course code/name | `ITS200-2` / `Pending Course Name - ITS200-2` |
| section | `T306` |
| professor name | Testing Professor |
| scheduled_start | 2026-06-17T12:50:00 |
| scheduled_end | 2026-06-17T14:00:00 |
| actual_start | 2026-06-17T13:14:21.808324 |
| actual_end | 2026-06-17T13:22:51.035819 |
| session_status | finalized |
| number of enrolled students | 40 |
| number of student_session_records | 40 |
| number of attendance_events | 33 |
| number of confirmed records | 40 |
| CSV export should be available based on session_status | Yes. The session is `finalized`, and the frontend enables Blackboard-ready CSV export after finalization. |

### Final Status Distribution

| Final status | Count |
|---|---:|
| absent | 7 |
| present | 33 |

### System Assessment Distribution

| System assessment | Count |
|---|---:|
| absent | 7 |
| attendance_warning | 8 |
| requires_review | 22 |
| valid_presence | 3 |

### Event Type Distribution

| Event type | Count |
|---|---:|
| time_in | 33 |

## 7. Sample Student Evidence Timeline

Sample student selected from session `4`.

| Field | Value |
|---|---|
| student number | 2025103040 |
| student name | Evans, Nora |
| final_status | present |
| system_assessment | valid_presence |
| time_in | 2026-06-17T13:14:34.162698 |
| time_out | Not Available |
| total_presence_minutes | 8 |
| total_outside_minutes | 0 |
| break_count | 0 |
| late_minutes | 0 |
| confirmed_by_professor | true |

### Chronological Event Timeline

| event_type | event_time | event_source | notes |
|---|---|---|---|
| time_in | 2026-06-17T13:14:34.162698 | facial_recognition | Auto Capture recognized Evans, Nora. |

## 8. Chapter 4 Writing Notes

### What Live Database Evidence Can Be Claimed

- The live V2 PostgreSQL database was reachable from inside the Docker backend container.
- The inspection transaction was read-only.
- The live V2 database contains populated V2 entities for users, professors, students, courses, rooms, classes, enrollments, face profiles, face embeddings, attendance sessions, session records, attendance events, and professor overrides.
- The live database contains 5 attendance sessions: 2 finalized, 2 in progress, and 1 under review.
- The live database contains attendance evidence events for `time_in`, `break_out`, `break_in`, and `manual_attendance`.
- The live database contains student session records with final statuses, system assessments, professor confirmations, presence minutes, outside minutes, break counts, and late minutes.
- A representative finalized session exists and includes 40 enrolled students, 40 student session records, 33 attendance events, and 40 confirmed records.
- For finalized session `4`, Blackboard-ready CSV export should be available based on the implemented frontend finalization/export behavior.

### What Cannot Be Claimed From This Inspection

- This inspection does not prove recognition accuracy, false positive rate, false negative rate, or biometric benchmark performance.
- This inspection does not prove stress-test, concurrency-test, or large-scale performance results.
- This inspection does not prove direct Blackboard API integration; the evidence supports Blackboard-ready CSV export, not API sync.
- This inspection does not prove that all in-progress sessions are valid or intentionally still open.
- This inspection does not prove usability outcomes or user acceptance results.

### Limitations

- The inspection was a point-in-time database snapshot from 2026-06-19.
- The database is not globally read-only; only this inspection transaction was read-only.
- Counts may change after this report if professors use the deployed system.
- The selected sample session is representative because it is finalized, but it is still only one session.
- Some event labels differ from the requested generic labels; the live database uses `manual_professor` as an event source rather than plain `manual`.
