# FRAS V2 QA Test Plan

## Test Strategy

FRAS V2 testing focuses on the complete professor-only attendance workflow:

```text
Professor Login
-> Classes
-> Class Roster / Face Profile Registration
-> Live Session Monitoring
-> Post Session Review
-> Student Evidence
-> Finalize Attendance
-> CSV Export
-> Session History
```

The strategy combines manual functional testing, integration testing against the V2 PostgreSQL database, UI consistency checks, and negative testing for locked or invalid states. Camera and facial recognition tests should be run on a real browser with camera permission granted.

Testing should confirm that V2 behaves as an instructor-facing classroom presence monitoring system, not an admin dashboard, student portal, or V1 room-based workflow.

## Scope

This plan covers the professor-only FRAS V2 system, including login, classes, roster, student history, face profile registration/update, live monitoring, auto capture, session break, return detection mode, review/finalization, student evidence, session history, and CSV export.

## In Scope Features

- Professor login using seeded professor accounts.
- Today's Classes / Classes dashboard.
- Current, upcoming, completed, and assigned class display.
- Class-specific Student List / Class Roster.
- Student Attendance History for a selected class.
- Register / Update Face Data.
- Live Session Monitoring.
- Camera preview and manual capture.
- Auto Capture start/stop behavior.
- Session Break behavior.
- Return Detection Mode during Session Break.
- Live roster status updates.
- Recognition activity feed.
- Manual attendance modal.
- Student quick detail drawer.
- Student break in / break out controls.
- Post Session Review.
- Student Evidence page.
- Attendance override.
- Mark Excused through override/manual workflows.
- Accept Current Status / reviewed record behavior.
- Finalize Attendance.
- Blackboard CSV export.
- Class-specific Session History.
- Professor-wide Session History from the sidebar.
- Route guards and backend locking while a session is on break.

## Out of Scope Features

- Admin dashboard.
- Admin settings.
- User management screens.
- Student portal.
- Student login.
- Faculty records management.
- Course management.
- Room schedule editor from V1.
- V1 room-based attendance flow.
- Production containerization validation.
- Blackboard live API sync, unless added later.

## Test Environment

### Local Backend

- OS: Windows development machine.
- Backend: FastAPI app launched from repo root.
- Database: PostgreSQL local database `fras_v2`.
- Environment: `.env` with `DATABASE_URL`.
- Command:

```powershell
.\.venv\Scripts\python.exe backend.py
```

### Local Frontend

- App: Angular/Ionic frontend.
- Path:

```powershell
cd facial-attendance
npm start
```

- Browser:
  - Chrome or Edge recommended.
  - Camera permission must be granted for Live Session and Face Profile Registration.

### Build Check

```powershell
cd facial-attendance
npm run build
```

Known non-blocking warnings may include Ionic/StenciI glob warning and bundle budget warning.

## Test Data

Use seeded V2 data from the local PostgreSQL database.

### Required Seed Data

- Professor accounts from `FRAS-prof-database.docx`.
- Course records from the professor schedule document.
- Room records, including special values like `ONLINE` if present.
- Class records linked to professor, course, section, room, day, start time, and end time.
- Sample students.
- Enrollments for selected classes.
- Special test professor with classes across Monday to Sunday and morning to night slots.

### Suggested Development Accounts

| Account | Email | Password | Purpose |
|---|---|---|---|
| Test Professor | `test.professor@fras.local` | `password123` | Edge case testing across all days and time slots |
| Seeded Professors | From database seed | Development password from seed docs | Real faculty schedule testing |

### Required Test Conditions

- At least one professor with classes today.
- At least one professor with no classes today but with future classes.
- At least one class with enrolled students.
- At least one student with no face profile.
- At least one student with registered face profile.
- At least one completed session.
- At least one under-review session.
- At least one finalized session.
- At least one session with late, absent, excused, and reviewed records.

## Test Execution Order

1. Verify database seed and local environment.
2. Verify professor login.
3. Verify Classes dashboard.
4. Verify Class Roster and Student Attendance History.
5. Verify Face Profile Registration / Update.
6. Verify Live Session start.
7. Verify manual capture and auto capture.
8. Verify manual attendance behavior.
9. Verify Session Break and Return Detection Mode.
10. Verify End Session and Post Session Review.
11. Verify Student Evidence.
12. Verify overrides, excused status, and reviewed records.
13. Verify Finalize Attendance.
14. Verify CSV Export.
15. Verify class-specific Session History.
16. Verify professor-wide Session History from sidebar.
17. Run negative and edge case tests.
18. Run final build check.

## Entry Criteria

- Backend starts without fatal errors.
- Frontend starts or builds successfully.
- Database has V2 tables and seeded professor/class/student data.
- Test professor can log in.
- At least one test class has enrolled students.

## Exit Criteria

- All critical priority test cases pass.
- No blocker prevents the full flow from Login to CSV Export.
- Session Break locks controls and navigation correctly.
- Finalized attendance exports professor-reviewed final statuses.
- Any remaining gaps are documented in `COVERAGE_MATRIX.md`.

## Risk Areas

- Camera permission and browser device behavior.
- Facial recognition confidence variance.
- Duplicate face embeddings or stale face profiles.
- Manual attendance interacting with automatic recognition.
- Session Break security if professor leaves laptop unattended.
- CSV format acceptance by Blackboard.
- Route guard behavior during browser back/refresh.
- Professor-wide Session History accidentally showing another professor's sessions.

