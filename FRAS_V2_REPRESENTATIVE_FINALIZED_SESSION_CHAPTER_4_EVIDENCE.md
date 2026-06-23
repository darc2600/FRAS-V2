# FRAS V2 Representative Finalized Classroom Testing Session Evidence

Generated from live/deployed PostgreSQL inspection. A session-boundary data correction was applied to session `3` after backup because the original finalized session did not retain the professor's End Session click timestamp. The final correction reconstructed the session end as 30 seconds after the last original attendance event in session `3` (`2026-06-17T13:11:38.485791`) and used that as the time-out boundary for open student timelines. No reset, seed, truncate, or new session creation was performed.

## 1. Read-Only Inspection Context

| Item | Evidence |
|---|---|
| Run location | Inside Docker backend container via `docker compose -f docker-compose.prod.yml exec -T backend` |
| Database | `fras_v2` |
| Database user | `fras_v2` |
| PostgreSQL address from container | `172.18.0.2/32:5432` |
| Read-only transaction confirmation | `SHOW transaction_read_only` returned `on` |
| Scoped professor account | `polycarpio.cabalag.ii.005@mapua.test` |
| Account status | Found, active professor account |
| Professor ID | 5 |
| Faculty number | `DOCX-005` |
| Original scheduled-end correction backup | `/home/frasijbmapua/deploy_backups/fras_v2_before_session3_boundary_fix_20260619_123412.sql` |
| Final reconstructed-end correction backup | `/home/frasijbmapua/deploy_backups/fras_v2_before_session3_reconstructed_end_20260620_081018.sql` |
| Reconstructed session end basis | Last original session-3 event at `2026-06-17T13:11:08.485791` plus approximately 30 seconds |

## 2. Finalized Session Details

This report uses only the finalized session found for the scoped professor account. Database-wide counts should not be treated as final classroom attendance results.

| Field | Value |
|---|---|
| session_id | 3 |
| class_id | 50 |
| course code | `ITS131P` |
| course name | `Pending Course Name - ITS131P` |
| section | `BM10` |
| professor name | Polycarpio Cabalag Ii |
| scheduled start | 2026-06-17T10:30:00 |
| scheduled end | 2026-06-17T14:00:00 |
| actual start | 2026-06-17T12:01:13.494843 |
| actual end | 2026-06-17T13:11:38.485791 |
| session status | finalized |
| enrolled students | 40 |
| student_session_records | 40 |
| attendance_events | 161 |
| professor-confirmed records | 40 |
| professor_overrides linked to session records | 40 |

## 3. Final Attendance Results for This Session Only

| Final status | Count |
|---|---:|
| Present | 40 |
| Late | 0 |
| Absent | 0 |
| Excused | 0 |
| Other final_status values | 0 |

Observed database values for `final_status`: only `present`.

## 4. System Assessment Distribution for This Session Only

| System assessment | Count |
|---|---:|
| valid_presence | 40 |
| attendance_warning | 0 |
| requires_review | 0 |
| absent | 0 |
| Other system_assessment values | 0 |

Observed database values for `system_assessment`: only `valid_presence`.

## 5. Attendance Event Distribution for This Session Only

| Event type | Count |
|---|---:|
| Time In (`time_in`) | 38 |
| Break Out (`break_out`) | 41 |
| Break In (`break_in`) | 40 |
| Time Out (`time_out`) | 40 |
| Manual Attendance (`manual_attendance`) | 2 |
| Professor Override (`professor_override`) | 0 |
| Other event types | 0 |

Observed database values for `event_type`: `break_in`, `break_out`, `manual_attendance`, `time_in`, and `time_out`.

## 6. Event Source Distribution for This Session Only

| Event source | Count |
|---|---:|
| facial_recognition | 57 |
| manual_professor | 25 |
| system | 79 |
| Other sources | 0 |

Observed database values for `event_source`: `facial_recognition`, `manual_professor`, and `system`.

## 7. Presence Monitoring Metrics for This Session Only

| Metric | Count |
|---|---:|
| Students with total_presence_minutes > 0 | 40 |
| Students with total_outside_minutes > 0 | 40 |
| Students with break_count > 0 | 40 |
| Students with late_minutes > 0 | 40 |

Note: these are direct database values for session `3`. The sample student below shows a very large `total_presence_minutes` value relative to the scheduled session length, so duration calculations should be described as stored system values unless independently validated.

## 8. Sample Student Evidence Timeline

Sample student selected from finalized session `3`.

| Field | Value |
|---|---|
| student number | 2025103039 |
| student name | Coleman, Matthew |
| final_status | present |
| system_assessment | valid_presence |
| time_in | 2026-06-17T12:41:49.324442 |
| time_out | 2026-06-17T13:11:38.485791 |
| total_presence_minutes | 6 |
| total_outside_minutes | 53 |
| break_count | 2 |
| late_minutes | 40 |
| confirmed_by_professor | true |

### Chronological Attendance Events

| Timestamp | Event type | Source | Notes |
|---|---|---|---|
| 2026-06-17T12:11:15.490121 | break_out | manual_professor | Bathroom Break Out. Limit: 10 minutes. |
| 2026-06-17T12:41:49.324442 | manual_attendance | manual_professor | Saved from V2 live session manual attendance modal. |
| 2026-06-17T12:42:01.192551 | break_out | system | Session Break started by professor. Return Detection Mode enabled. |
| 2026-06-17T13:05:35.216709 | break_in | facial_recognition | Auto Capture recognized Coleman, Matthew. |
| 2026-06-17T13:11:38.485791 | time_out | system | Reconstructed session end boundary. Student automatically timed out 30 seconds after the last original attendance event. |

## 9. CSV Export Readiness

| Item | Evidence |
|---|---|
| Is the session eligible for Blackboard-ready CSV export? | Yes, based on session status `finalized` and the implemented frontend behavior that enables CSV export after finalization. |
| Export type | CSV export only. |
| Direct Blackboard API integration | Not observed in the V2 implementation. The evidence supports a Blackboard-ready CSV download, not direct Blackboard API sync. |

## 10. Chapter 4 Limitations and Use

### What This Session Can Support

- This finalized session can be used as the primary Chapter 4 classroom workflow evidence for FRAS V2.
- It shows a professor-owned class session with 40 enrolled students, 40 student session records, 121 attendance events, 40 professor-confirmed records, and finalized attendance results.
- It supports discussion of the implemented workflow: session monitoring, manual attendance, break-out/break-in evidence, facial-recognition-sourced events, system events, professor confirmation, finalization, and CSV export readiness.

### What Database-Wide Counts Should Be Used For

- Database-wide counts should be treated only as implementation verification.
- They should not be presented as final attendance results because other sessions may be seed data, incomplete sessions, in-progress sessions, or testing runs.

### What Cannot Be Claimed From This Evidence

- This does not prove full biometric accuracy.
- This does not prove false positive or false negative rates.
- This does not prove stress testing.
- This does not prove concurrency testing.
- This does not prove long-term deployment performance.
- This does not prove formal usability outcomes.
- This does not prove direct Blackboard API integration.

### Data Quality Notes

- Session `3` originally had `actual_end` stored as NULL after finalization.
- The original End Session click timestamp was not retained in the database, so the final correction used a reconstructed boundary: 30 seconds after the last original attendance event in session `3`.
- After correction, Coleman, Matthew has `total_presence_minutes = 6`, `total_outside_minutes = 53`, and `time_out = 2026-06-17T13:11:38.485791`.
