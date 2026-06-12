1. Project Title

FRAS V2 — Classroom Presence Monitoring using Facial-Recognition Embeddings


2. Revised System Description

FRAS V2 is an instructor-operated classroom presence monitoring system that uses facial recognition embeddings to record, evaluate, and finalize student presence during scheduled class sessions. The system captures raw recognition events, aggregates them into per-student session records (presence minutes, outside minutes, break counts, and late arrival minutes), and provides a post-session review workflow in which the professor can confirm or override automated assessments before finalizing attendance for export.


3. Problem Addressed by FRAS V2

Large lecture and laboratory classes require accurate, low-overhead attendance tracking that reflects not only whether a student was present but how long they remained in the monitored environment. FRAS V2 addresses the need for automated evidence-based attendance that can:

- Detect student entry (time-in) and departure (time-out),
- Track temporary absences/breaks and measure outside duration,
- Compute validated presence duration for fairness-aware attendance decisions,
- Provide per-student evidence and a controlled professor review/finalization flow for high-integrity records.


4. Main Difference Between FRAS V1 and FRAS V2

FRAS V1 focused on single-event facial recognition to mark attendance. FRAS V2 reframes attendance as an event-driven, session-based presence-monitoring problem. Key changes in V2:

- Sessions: attendance is tracked per scheduled session (start, in-progress, on-break, under-review, finalized).
- Event model: multiple event types (time_in, break_out, break_in, time_out, manual_attendance) are logged and used to compute presence/outside durations.
- Post-session review: a dedicated review and finalize workflow lets professors verify or override system assessments before export.
- Embedding store: recognition uses embeddings (DeepFace) and similarity scoring rather than single-shot local matching.


5. Target User and System Scope

Target user: Professors / Instructors who manage classroom attendance.

In-scope (implemented):

- Professor login and authenticated UI flows,
- Viewing today’s classes and starting live sessions,
- Registering/updating student face profiles (multi-angle uploads),
- Live recognition (auto and manual capture), break management, post-session review and finalization,
- CSV export for LMS (Blackboard-compatible output in the UI).

Out of scope (explicitly not implemented):

- Student-facing portal or student login,
- Full admin dashboard or comprehensive user-management UI,
- Course management workflows beyond seeded/import utilities.


6. Final Professor Workflow (End-to-End)

1. Login as professor (receive authentication token).
2. Open Today’s Classes and select a scheduled class.
3. Open Class Roster — review students and face-profile statuses.
4. Register or update student face profiles (upload multi-angle images; front image required).
5. Start live session (system creates session and student-session records).
6. During session:
   - Auto-capture sends frames to recognition; confident matches may be recorded as events.
   - Manual capture allows the professor to record attendance evidence when needed.
   - Start Break: professor initiates a session break; system marks active students as out (break_out events) and enters return-detection mode.
   - Students returning are detected as break_in events and aggregated into the record.
7. End session: professor ends the live session; system moves session to review state and recalculates aggregated presence metrics.
8. Post-session review: professor inspects roster and per-student evidence, applies manual attendance or overrides, and confirms individual records as needed.
9. Finalize attendance: once satisfied, professor finalizes the session; records are locked and CSV export becomes available.
10. Export CSV: professor downloads Blackboard-compatible CSV for LMS upload.

Each professor action that modifies attendance results in persisted records and event logs; finalization locks the session and confirms records.


7. Implemented System Modules

FRAS V2 implements three logical layers:

- Recognition & Embedding Service: extracts facial embeddings from images and compares them against enrolled embeddings to find candidate matches (operational use of an embedding model).
- Session & Attendance Service: event ingestion, session lifecycle management (start, break, end, finalize), per-student record recalculation (presence/outside minutes, break counts, late minutes), and professor override handling.
- UI & Export Layer: professor-facing Angular UI for live monitoring, student evidence review, and Blackboard-compatible CSV export.

All modules are integrated into a web service so a professor can operate the full cycle from login to CSV export.


8. Attendance and Presence Monitoring Logic

Core principles implemented:

- Event-first model: attendance is derived from timestamped events (time_in, break_out, break_in, time_out, manual_attendance, etc.).
- Presence aggregation: the system computes total presence minutes by summing intervals between inside periods and bounding them by the session end.
- Outside duration: intervals between break_out and break_in are summed separately as outside minutes.
- Presence ratio: presence minutes are compared to monitored session minutes to drive a quantitative assessment.
- Late arrival: the time between scheduled session start and first time_in is measured; long late arrivals may lead to an absent assessment subject to later override.
- System assessments: based on presence ratio and lateness thresholds, each student record is assigned a system assessment (e.g., valid_presence, attendance_warning, requires_review, absent) and a final status (present, late, absent, excused).
- Professor confirmations: a confirmed record overrides system assessment and sets final status accordingly.

Thresholds and exact policy parameters are implemented in the attendance service; any configurable values should be verified in runtime settings. (Needs Verification)


9. Session Break and Return Detection Logic

Implemented behavior:

- Starting a break transitions the session into an "on-break" state and records `break_out` events for students who are currently recorded as present or late.
- While on break, manual attendance actions are locked; the system accepts only facial-recognition-based `break_in` events for students returning from break.
- Ending a break requires professor authentication (password verification) and returns the session to the normal in-progress state.

This design enforces a controlled return-detection mode during breaks so that return evidence is captured as discrete break-in events rather than free-form manual edits.


10. Student Evidence and Post-Session Review

What the system provides to support review:

- Per-student event timeline: raw events (timestamps, types, recognition confidence, notes) for each session.
- Aggregated metrics: computed presence minutes, outside minutes, break count, late minutes, requires_review flags, and human-readable review reasons.
- Professor actions: confirm a record, mark excused, apply manual attendance entries, and perform final overrides (recorded in an override audit log).
- Finalization: finalizing a session confirms all session records and prevents further automated or manual changes.

These features allow the professor to reconcile automatic recognition with contextual knowledge before producing a final attendance record.


11. Database / Data Model Summary

The implemented data model captures the session/event/record semantics required for auditability and review. Principal entities:

- Users & Professors: authenticated users and professor metadata.
- Students & Enrollments: student identity and enrollment in classes.
- Classes & Schedule: scheduled class instances with day/time and room.
- Student Face Profiles & Embeddings: stored multi-angle images and embedding vectors used for recognition.
- Attendance Sessions: session lifecycle records (scheduled and actual start/end, status, finalized_at).
- Student Session Records: aggregated per-student session outcomes and metrics (final_status, system_assessment, presence/outside minutes, break_count, late_minutes, confirmed flags).
- Attendance Events: ordered event log entries used to derive metrics; includes event type, time, source, recognition confidence, and notes.
- Professor Overrides / Audit: records of manual overrides and the professor who applied them.

The model supports auditability (raw events are retained) and computation (aggregated fields are recalculated from events as needed).


12. Backend and Frontend Architecture Summary

- Backend: a web API service exposing session, roster, recognition, and review endpoints. The recognition flow uses an embedding extraction component and similarity scoring to match enrolled students. The backend orchestrates the session lifecycle and performs recalculations and persistence.

- Frontend: a professor-facing single-page application providing views for Today’s Classes, Live Session monitoring, Class Roster, Face Profile registration, Student Evidence, Post-Session Review, Session History, and CSV export. The UI calls authenticated API endpoints and implements controls for starting/ending sessions, capturing faces, and finalizing attendance.

The architecture is synchronous API-driven: the frontend initiates recognition or event creation, the backend validates and persists events, and the frontend renders updated session state.


13. CSV Export and Blackboard Use

- The system includes a Blackboard-compatible CSV export mechanism available after a session is finalized.
- Export is triggered from the post-session review UI and produces a CSV file formatted for import into Blackboard-style LMS systems.
- The export requires a finalized session to ensure the data is stable and auditable.

Detailed mapping of CSV columns and Blackboard field semantics should be verified with the target LMS import requirements. (Needs Verification)


14. QA and Testing Summary

- Unit and integration tests exercise core V2 flows (session start, event ingestion, recalculation, finalize) and recognition edge cases.
- Seed and verification scripts are available to populate realistic test data for instructor schedules, sample students, and integration scenarios.
- Frontend UI components for the professor workflow are present and exercised by integration checks, but local build/release details should be confirmed in the target environment. (Needs Verification)


15. Known Limitations

- Recognition reliability: automated recognition quality depends on the embedding model and environmental factors (lighting, occlusion). Manual capture and professor review are essential mitigations.
- Student-facing functionality is not implemented — students cannot log in or review their records through the system.
- Some operational features (secure password hashing presence in runtime, deployment environment variables, full LMS sync hooks) require verification in the deployment context. (Needs Verification)
- Policy thresholds (e.g., minutes to classify late/absent, presence ratio cutoffs) are implemented but should be validated against institutional policy or instructor preference. (Needs Verification)


16. Suggested Chapter Mapping (for thesis)

- Chapter 1 — Problem Statement & Objectives: introduce automated presence monitoring and the motivation for FRAS V2.
- Chapter 2 — Related Work: position FRAS among facial-recognition attendance and presence monitoring systems.
- Chapter 3 — System Design: architecture diagrams, event model, and data model (session/event/record design).
- Chapter 4 — Implementation: embedding extraction and similarity, session lifecycle logic, break/return detection, and review/finalize workflow.
- Chapter 5 — Evaluation & QA: test harness, seeded integration datasets, typical recognition cases, limitations and error analysis.
- Chapter 6 — Conclusions & Recommendations: lessons learned, deployment considerations, and future work.
- Appendices: sample CSV export, the V2 database schema (summary), seed data overview, and representative session/event timelines. (Include raw schema and seed script references in appendix if needed.)


Notes and next steps:

- Items marked "Needs Verification" indicate repository or runtime details that should be confirmed before citing them in a thesis (deployment configuration, exact policy thresholds, and LMS mapping).
- If you want, I can produce a condensed ChatGPT system prompt version of this content or an appendix listing specific API endpoints and example request/response payloads for reproducibility.