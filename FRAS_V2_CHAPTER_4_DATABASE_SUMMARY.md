# FRAS V2 Chapter 4 Database Summary

Generated from safe read-only inspection on 2026-06-19.

## Database Access Status

Live V2 PostgreSQL database: Needs Verification.

Reason: The active `.env` file contains:

```text
DATABASE_URL=postgresql://fras_v2:change-this-v2-password@db:5432/fras_v2
```

When safe read-only database scripts were run from the local shell, psycopg2 failed with:

```text
could not translate host name "db" to address: Name or service not known
```

This indicates that `db` is a Docker-internal service hostname and was not resolvable from the current local shell session. No database reset, seed, truncate, or write operation was performed.

## V2 Schema Evidence

The V2 PostgreSQL schema is defined in `database/v2_schema.sql`. It includes these V2-relevant tables:

- `users`
- `professors`
- `students`
- `courses`
- `rooms`
- `classes`
- `enrollments`
- `student_face_profiles`
- `attendance_sessions`
- `student_session_records`
- `attendance_events`
- `professor_overrides`
- `blackboard_sync_logs`

Observed schema note: `database/v2_schema.sql` contains `student_face_profiles.embedding_json`. A separate `student_face_embeddings` table exists in the local SQLite fallback database and is used by V2 face audit scripts, but it is not created in the visible `database/v2_schema.sql` file inspected here. This should be treated as Needs Verification against the live/migrated V2 Postgres database.

## Local SQLite Fallback Counts

Because the live V2 Postgres database was not reachable from the local shell, `attendance.db` was inspected in read-only SQLite mode as fallback evidence. These numbers are not confirmed live V2 Postgres rows.

Command used:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('file:attendance.db?mode=ro', uri=True); ..."
```

Observed local SQLite table counts:

| Item requested | Count / status |
|---|---:|
| users | 12 |
| professors | Not Available - table missing in local SQLite fallback |
| students | 150 |
| courses | 93 |
| rooms | 4 |
| classes | 2 |
| enrollments | 53 |
| student_face_profiles | Not Available - table missing in local SQLite fallback |
| student_face_embeddings | 54 |
| attendance_sessions | Not Available - table missing in local SQLite fallback |
| student_session_records | Not Available - table missing in local SQLite fallback |
| attendance_events | Not Available - table missing in local SQLite fallback |
| professor_overrides | Not Available - table missing in local SQLite fallback |
| finalized sessions | Not Available - `attendance_sessions` table missing in local SQLite fallback |
| sessions under review | Not Available - `attendance_sessions` table missing in local SQLite fallback |
| sessions in progress | Not Available - `attendance_sessions` table missing in local SQLite fallback |
| sessions on break | Not Available - `attendance_sessions` table missing in local SQLite fallback |
| records by final_status | Not Available - `student_session_records` table missing in local SQLite fallback |
| events by event_type | Not Available - `attendance_events` table missing in local SQLite fallback |
| records with presence duration | Not Available - `student_session_records` table missing in local SQLite fallback |
| records with outside duration | Not Available - `student_session_records` table missing in local SQLite fallback |
| records with break_count greater than 0 | Not Available - `student_session_records` table missing in local SQLite fallback |

## Read-Only Verification Scripts Attempted

| Script | Status | Output summary |
|---|---|---|
| `database/check_v2_database.py` | Failed / Needs Verification | Could not resolve Postgres host `db`. |
| `database/check_v2_seed.py` | Failed / Needs Verification | Could not resolve Postgres host `db`. |
| `database/check_v2_roster_counts.py` | Failed / Needs Verification | Could not resolve Postgres host `db`. |
| `database/verify_v2_integration_seed.py` | Failed / Needs Verification | Could not resolve Postgres host `db`. |
| `database/audit_v2_face_data.py` | Failed / Needs Verification | Could not resolve Postgres host `db`. |

## Database Evidence Conclusion

- The V2 schema and deployment files indicate a PostgreSQL V2 database design.
- The configured local shell could not connect to the live V2 Postgres database because `db` is not resolvable outside Docker.
- The available local SQLite fallback database does not contain the V2 session tables needed to report live session/session-record/event counts.
- Therefore, current live V2 database counts for sessions, records, events, final statuses, event types, presence durations, outside durations, and break counts are Not Available / Needs Verification.
