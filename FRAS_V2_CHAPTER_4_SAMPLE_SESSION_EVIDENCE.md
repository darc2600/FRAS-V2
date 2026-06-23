# FRAS V2 Chapter 4 Sample Session Evidence

Generated from safe read-only inspection on 2026-06-19.

## Sample Session Status

No sample session found.

Exact reason:

- The live V2 PostgreSQL database could not be reached from the local shell because the configured `.env` value uses Docker-internal host `db`.
- Read-only script attempts failed with: `could not translate host name "db" to address: Name or service not known`.
- The local fallback SQLite database `attendance.db` was inspected in read-only mode, but it does not contain the V2 session tables `attendance_sessions`, `student_session_records`, `attendance_events`, or `professor_overrides`.
- No session creation, seed, reset, or mutation script was run because the user requested no database modification.

## Requested Sample Session Fields

| Field | Evidence |
|---|---|
| session id | No sample session found |
| class/course/section | Not Available |
| professor | Not Available |
| scheduled start/end | Not Available |
| actual start/end | Not Available |
| session status | Not Available |
| number of enrolled students | Not Available for a sample session |
| number of student_session_records | Not Available - `student_session_records` unavailable in local fallback |
| number of attendance_events | Not Available - `attendance_events` unavailable in local fallback |
| number of manual attendance events | Not Available - `attendance_events` unavailable in local fallback |
| number of facial recognition events | Not Available - `attendance_events` unavailable in local fallback |
| number of break_out events | Not Available - `attendance_events` unavailable in local fallback |
| number of break_in events | Not Available - `attendance_events` unavailable in local fallback |
| number of professor overrides | Not Available - `professor_overrides` unavailable in local fallback |
| number of confirmed records | Not Available - `student_session_records` unavailable in local fallback |
| final_status distribution | Not Available - `student_session_records` unavailable in local fallback |
| system_assessment distribution | Not Available - `student_session_records` unavailable in local fallback |
| sample student evidence timeline | Not Available - no sample session found |
| sample computed presence duration | Not Available - no sample session found |
| sample outside duration | Not Available - no sample session found |
| sample break count | Not Available - no sample session found |
| whether session was finalized | Not Available - no sample session found |
| whether Blackboard CSV export would be available | Needs Verification for a live sample session. Implementation evidence shows frontend CSV export becomes available after finalization in `post-session-review.component.ts`. |

## Implementation Evidence for What a Sample Session Would Contain

Although no live sample session was available, the implementation supports these sample-session fields:

- `v2/models.py` defines session responses, student records, attendance events, review summaries, and history rows.
- `v2/repository.py` reads/writes `attendance_sessions`, `student_session_records`, `attendance_events`, and professor override-related updates.
- `v2/service.py` computes session detail, review summary, final status, system assessment, presence minutes, outside minutes, break counts, review flags, finalization, and history.
- `facial-attendance/src/app/v2/pages/student-evidence/student-evidence.component.ts` displays a per-student timeline using review/detail data.
- `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` supports finalization and browser-side Blackboard-ready CSV export after finalization.

## Safe Verification Not Performed

The file `database/verify_v2_full_integration.py` can create a representative session and test finalization/CSV behavior, but it was not run because it writes session data. It creates sessions, attendance events, manual excused overrides, ends sessions, and finalizes sessions.

Status: Not Run, by design, to respect the no-modification rule.
