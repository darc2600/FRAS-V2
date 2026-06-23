# FRAS V2 Chapter 4 Testing Results

Generated from code inspection and safe verification commands on 2026-06-19. No database reset, seed, truncate, or product-code modification was performed.

## Verification Summary

| File path | Purpose | Command used | Result | Important output summary | Reason if not run |
|---|---|---|---|---|---|
| `tests/test_v2_recognition_decision.py` | Unit tests for V2 recognition decision rules: strong match, below threshold, ambiguous top matches, and margin behavior. | `.venv\Scripts\python.exe -m pytest tests\test_v2_recognition_decision.py -q` | Passed | `5 passed in 14.56s` | Not applicable |
| `tests/test_v2_api.py` | Smoke/integration test for route registration, today's classes, start session, event creation, review, break start/end, and session end. | Not run | Not Run | The file was inspected. It calls `init_v2_database(["--force"])` and `seed_v2_database([])` in `setup_module()`. | Not run because the user explicitly requested no reset and no seed unless explicitly asked. |
| `database/verify_v2_integration_seed.py` | Read-only seed/integration verification: database identity, row counts, faculty/test professor login, today classes, schedule, roster. | `.venv\Scripts\python.exe database\verify_v2_integration_seed.py` | Failed / Needs Verification | Script attempted to connect to Postgres and failed: `could not translate host name "db" to address: Name or service not known`. TensorFlow informational logs also appeared before the DB failure. | Configured `.env` has `DATABASE_URL=postgresql://...@db:5432/fras_v2`; host `db` is Docker-internal and not resolvable from this local shell. |
| `database/verify_v2_full_integration.py` | Full integration exercise including login, class schedule/roster, face context, session creation, attendance events, finalization, history, CSV filename/content, and recognition attempt. | Not run | Not Run | The file was inspected. It creates policy sessions, events, manual excused overrides, ends sessions, and finalizes sessions. | Not run because it writes session data and the user requested no data modification. |
| `database/check_v2_database.py` | Lists public database tables. | `.venv\Scripts\python.exe database\check_v2_database.py` | Failed / Needs Verification | Failed with `could not translate host name "db" to address: Name or service not known`. | Configured Postgres host `db` is not reachable from local shell. |
| `database/check_v2_seed.py` | Counts V2 seed data and lists classes. | `.venv\Scripts\python.exe database\check_v2_seed.py` | Failed / Needs Verification | Failed with `could not translate host name "db" to address: Name or service not known`. | Configured Postgres host `db` is not reachable from local shell. |
| `database/check_v2_roster_counts.py` | Checks student totals, duplicates, managed sample students, non-online active classes, and active sample enrollments. | `.venv\Scripts\python.exe database\check_v2_roster_counts.py` | Failed / Needs Verification | Failed with `could not translate host name "db" to address: Name or service not known`. | Configured Postgres host `db` is not reachable from local shell. |
| `database/audit_v2_face_data.py` | Audits active face profiles, embeddings, duplicate active profiles, duplicate embeddings, reused source paths, exact duplicate embeddings, and high-similarity pairs. | `.venv\Scripts\python.exe database\audit_v2_face_data.py` | Failed / Needs Verification | Failed with `could not translate host name "db" to address: Name or service not known`. | Configured Postgres host `db` is not reachable from local shell. |

## Completed or Supported

### Happy Path Testing

Supported by inspected code, especially `tests/test_v2_api.py`, but not safely run because it resets and seeds the database. The test exercises:

- Today's classes lookup.
- Professor schedule lookup.
- Session start.
- Student session record creation.
- Manual time-in event creation.
- Session review summary.
- Break start.
- Break end.
- End session into `under_review`.

Status: Supported by code; Needs Verification in current live database because the safe run was not performed.

### API Smoke Testing

Supported by `tests/test_v2_api.py::test_v2_routes_are_registered`, which checks that these V2 routes are registered:

- `/api/v2/professors`
- `/api/v2/professors/{professor_id}/today/classes`
- `/api/v2/professors/{professor_id}/schedule`
- `/api/v2/classes/{class_id}/sessions/start`
- `/api/v2/sessions/{session_id}/events`
- `/api/v2/sessions/{session_id}/review`

Status: Supported by code; not run because the test module setup resets/seeds the database.

### Database Seed Verification

Supported by `database/verify_v2_integration_seed.py`, `database/check_v2_seed.py`, and `database/check_v2_roster_counts.py`.

Observed run result: Needs Verification. The scripts were attempted where safe, but failed because the configured Postgres host `db` could not be resolved from the local shell.

### Session Lifecycle Validation

Supported by `tests/test_v2_api.py` and `database/verify_v2_full_integration.py`.

Status: Supported by code. Not safely run because available full lifecycle scripts reset/seed or create/finalize session data.

### Recognition Decision Rule Validation

Completed.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_v2_recognition_decision.py -q
```

Result:

```text
5 passed in 14.56s
```

### Integration Checking

Supported by `database/verify_v2_integration_seed.py` and `database/verify_v2_full_integration.py`.

Status: Needs Verification in the current live V2 Postgres database because `DATABASE_URL` points to Docker host `db`, which did not resolve from the local shell.

## Not Conducted or Not Supported

The following were not found as completed formal test evidence in the safe inspected/runnable set:

- Full frontend browser E2E testing: Not Conducted / Needs Verification.
- Stress testing: Not Conducted / Needs Verification.
- Concurrency testing: Not Conducted / Needs Verification.
- Large-scale recognition accuracy benchmarking: Not Conducted / Needs Verification.
- False positive / false negative analysis: Not Conducted / Needs Verification.
- Confusion matrix evaluation: Not Conducted / Needs Verification.
- Formal usability testing from code: Not Conducted / Needs Verification.

## V2 Happy Path Support Check

| Happy path step | Code/test support status | Evidence |
|---|---|---|
| Login | Supported | `facial-attendance/src/app/login/*`, `api/auth.py`, `POST /api/login` |
| Today's Classes | Supported | `V2TodaysClassesComponent`, `GET /api/v2/professors/{professor_id}/today/classes` |
| Class Roster | Supported | `V2ClassRosterComponent`, `GET /api/v2/classes/{class_id}/students` |
| Face Profile Registration/Update | Supported | `V2FaceProfileComponent`, `GET/POST /api/v2/classes/{class_id}/students/{student_id}/face-profile` |
| Start Live Session | Supported | `POST /api/v2/classes/{class_id}/sessions/start`; exercised in `tests/test_v2_api.py` but not run safely |
| Manual Attendance and/or Facial Recognition Capture | Supported | `POST /api/v2/sessions/{session_id}/manual-attendance`, `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{session_id}/events` |
| Session Break | Supported | `POST /api/v2/sessions/{session_id}/break/start`; exercised in `tests/test_v2_api.py` but not run safely |
| Return Detection | Supported | Live session break mode uses recognition/event APIs during `on_break` state |
| End Session | Supported | `POST /api/v2/sessions/{session_id}/end`; exercised in `tests/test_v2_api.py` but not run safely |
| Post-Session Review | Supported | `V2PostSessionReviewComponent`, `GET /api/v2/sessions/{session_id}/review` |
| Student Evidence | Supported | `V2StudentEvidenceComponent`, review/detail endpoints |
| Override or Mark Excused if needed | Supported | `POST /api/v2/sessions/{session_id}/manual-attendance`; statuses include `present`, `absent`, `late`, `excused` |
| Finalize Attendance | Supported | `POST /api/v2/sessions/{session_id}/finalize` |
| Export CSV | Supported in frontend | Browser-side CSV export from review/history data; no direct Blackboard API endpoint observed |
| Session History | Supported | `GET /api/v2/professors/{professor_id}/session-history`, `GET /api/v2/classes/{class_id}/session-history` |

Overall happy path status: Supported by implementation and inspected tests, but Needs Verification against the current live V2 Postgres database because safe DB access from the local shell failed.
