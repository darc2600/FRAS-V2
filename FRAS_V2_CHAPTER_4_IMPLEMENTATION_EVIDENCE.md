# FRAS V2 Chapter 4 Implementation Evidence

Generated from code inspection on 2026-06-19. This file summarizes observed implementation evidence only. Items that could not be verified from the active codebase are marked "Not Available" or "Needs Verification."

## 1. Implemented V2 System Overview

FRAS V2 is implemented as a professor-centered classroom presence monitoring system. Evidence:

- The default frontend route redirects to `/v2/classes`.
- Professor users are routed to `/v2/classes` after login.
- The V2 backend router is mounted under `/api/v2` with the tag `V2 Attendance`.
- V2 pages focus on professor class schedules, class rosters, face profile registration, live session monitoring, post-session review, evidence review, finalization, history, and CSV export.

Primary evidence files:

- `facial-attendance/src/app/app.routes.ts`
- `facial-attendance/src/app/login/login.component.ts`
- `facial-attendance/src/app/api.service.ts`
- `v2/api.py`
- `v2/service.py`
- `v2/repository.py`
- `v2/models.py`

## 2. Implemented V2 Modules

| Module | Frontend file path | Route | Purpose | Main buttons/actions | Backend API endpoints used | Related backend files |
|---|---|---|---|---|---|---|
| Login | `facial-attendance/src/app/login/login.component.ts`, `facial-attendance/src/app/login/login.component.html`, `facial-attendance/src/app/login/login.service.ts` | `/login` | Authenticates users and routes non-admin/professor users into the V2 professor workflow. | Sign In, show/hide password | `POST /api/login` | `api/auth.py`, `backend.py`, `services/db.py` |
| Today's Classes | `facial-attendance/src/app/v2/pages/todays-classes/todays-classes.component.ts/html/scss` | `/v2/classes`, `/v2/today` redirect, `/v2/schedule` | Shows professor's current/upcoming/completed classes for a selected date and schedule context. | Start Session, Start Monitor, View History, View Roster | `GET /api/v2/professors/{professor_id}/today/classes`, `GET /api/v2/professors/{professor_id}/schedule`, `GET /api/v2/professors`, `POST /api/v2/classes/{class_id}/sessions/start` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `v2/models.py` |
| Class Roster | `facial-attendance/src/app/v2/pages/class-roster/class-roster.component.ts/html/scss` | `/classes/:classId/students`, `/v2/classes/:classId/students` | Displays enrolled students, face profile status, recognition status, and student attendance history links. | Register/Update Face Profile, View History, search/filter roster | `GET /api/v2/classes/{class_id}/students`, `GET /api/v2/classes/{class_id}/students/{student_id}/history` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Face Profile Registration / Update | `facial-attendance/src/app/v2/pages/face-profile/face-profile.component.ts/html/scss` | `/classes/:classId/students/:studentId/face-profile`, `/v2/classes/:classId/students/:studentId/face-profile` | Captures multi-angle student face images and saves/updates the active V2 face profile. | Start Camera, Capture, auto capture toggle, Reset Captures, Register Face Profile, Update Face Profile, Back | `GET /api/v2/classes/{class_id}/students/{student_id}/face-profile`, `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `services/face_embeddings.py` |
| Live Session Monitoring | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss` | `/live-session/:sessionId` | Runs an active classroom monitoring session with roster, events, timers, camera recognition state, break state, and manual tools. | Capture Face, Start/Stop Recognition loop, Manual Attendance, Start Break, End Session, student drawer actions | `GET /api/v2/sessions/{session_id}`, `GET /api/v2/professors/{professor_id}/schedule`, `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{session_id}/events`, `POST /api/v2/sessions/{session_id}/manual-attendance`, `POST /api/v2/sessions/{session_id}/break/start`, `POST /api/v2/sessions/{session_id}/break/end`, `POST /api/v2/sessions/{session_id}/end` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `services/face_embeddings.py` |
| Manual Attendance | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss`, `facial-attendance/src/app/v2/components/v2-student-detail-drawer/*` | `/live-session/:sessionId`; also used in review | Allows professor to set student statuses manually during the live session or review. | Present, Absent, Late, Excused, Override, Save Manual Attendance | `POST /api/v2/sessions/{session_id}/manual-attendance` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `v2/models.py` |
| Facial Recognition Capture | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss` | `/live-session/:sessionId` | Captures a camera image, calls V2 recognition, and can record recognition attendance events. | Capture Face, Start/Stop Recognition, automatic capture loop | `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{session_id}/events` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `services/face_embeddings.py` |
| Session Break | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss` | `/live-session/:sessionId` | Changes session into break mode, records break-out events, and locks navigation during break. | Start Break, Unlock/End Break | `POST /api/v2/sessions/{session_id}/break/start`, `POST /api/v2/sessions/{session_id}/break/end` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `auth.guard.ts` |
| Return Detection Mode | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss` | `/live-session/:sessionId` when session status is `on_break` | Uses automatic face capture during break mode to detect returning students and record break-in evidence. | Return Detection Mode Active/Idle, End Break | `POST /api/v2/classes/{class_id}/recognize`, `POST /api/v2/sessions/{session_id}/events`, `POST /api/v2/sessions/{session_id}/break/end` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `services/face_embeddings.py` |
| Post-Session Review | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts/html/scss` | `/session-review/:sessionId`, `/v2/sessions/:sessionId/review` redirect | Reviews computed attendance after a session ends and before/after finalization. | View Evidence, Override Mode, Save Changes, Finalize Attendance, Export CSV, Go to History | `GET /api/v2/sessions/{session_id}/review`, `GET /api/v2/sessions/{session_id}`, `POST /api/v2/sessions/{session_id}/manual-attendance`, `POST /api/v2/sessions/{session_id}/finalize`, `GET /api/v2/professors/{professor_id}/schedule` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Student Evidence | `facial-attendance/src/app/v2/pages/student-evidence/student-evidence.component.ts/html/scss` | `/student-evidence/:sessionId/:studentId` | Shows one student's session evidence timeline, computed presence/outside time, break count, and review explanation. | Confirm Record, Override/Manual Status, Back to Review | `GET /api/v2/sessions/{session_id}/review`, `GET /api/v2/sessions/{session_id}`, `POST /api/v2/sessions/{session_id}/students/{student_id}/confirm`, `POST /api/v2/sessions/{session_id}/manual-attendance`, `GET /api/v2/professors/{professor_id}/schedule` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Mark Excused | `facial-attendance/src/app/v2/pages/live-session/live-session.component.ts/html/scss`, `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts/html/scss`, `facial-attendance/src/app/v2/components/v2-student-detail-drawer/*` | `/live-session/:sessionId`, `/session-review/:sessionId`, `/student-evidence/:sessionId/:studentId` | Allows professor to set a student's attendance status to excused through manual attendance/override status. | Excused quick status, Save Changes | `POST /api/v2/sessions/{session_id}/manual-attendance` | `v2/api.py`, `v2/service.py`, `v2/repository.py`, `v2/models.py` |
| Professor Override | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts/html/scss`, `facial-attendance/src/app/v2/components/v2-student-detail-drawer/*` | `/session-review/:sessionId`; also drawer in `/live-session/:sessionId` | Lets professor override system/computed status before finalization. | Override, Present, Absent, Late, Excused, Save Changes, Cancel | `POST /api/v2/sessions/{session_id}/manual-attendance` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Attendance Finalization | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts/html/scss` | `/session-review/:sessionId` | Locks session attendance after review and enables CSV export. | Finalize Attendance | `POST /api/v2/sessions/{session_id}/finalize` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Session History | `facial-attendance/src/app/v2/pages/session-history/session-history.component.ts/html/scss`, `facial-attendance/src/app/v2/pages/student-class-history/*` | `/session-history`, `/v2/history`, `/classes/:classId/session-history`, `/classes/:classId/students/:studentId/history` | Displays professor-wide, class-level, and student-level attendance history. | View Session Summary, View Evidence, Export Full History, filters | `GET /api/v2/professors/{professor_id}/session-history`, `GET /api/v2/classes/{class_id}/session-history`, `GET /api/v2/classes/{class_id}/students/{student_id}/history` | `v2/api.py`, `v2/service.py`, `v2/repository.py` |
| Blackboard-ready CSV Export | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts/html/scss`, `facial-attendance/src/app/v2/pages/session-history/session-history.component.ts/html/scss` | `/session-review/:sessionId`, `/session-history`, `/classes/:classId/session-history` | Generates browser-side CSV downloads from finalized session/review/history data. Direct Blackboard API upload is not implemented. | Export CSV, Export Full History | Uses existing review/history endpoints; CSV generation is in frontend code | `v2/service.py`, `v2/repository.py`; no direct Blackboard API backend endpoint observed |

## 3. Not Implemented in V2 Professor Workflow

The following are not part of the active V2 professor workflow observed in `app.routes.ts`, V2 pages, and `/api/v2` routes:

- Student portal: Not implemented in active V2 professor workflow.
- Student login workflow: Not implemented as a V2 student workflow; login exists but routes professor/non-admin users into `/v2/classes`.
- Full admin dashboard: Legacy/admin components exist, but V2-only mode in `backend.py` loads auth and V2 routers only. Not part of active V2 professor workflow.
- Full user management workflow: Legacy/admin user-management code exists outside the V2 professor workflow. Not part of active V2 workflow.
- Course management workflow: Legacy course/schedule APIs exist outside V2. Not part of active V2 professor workflow.
- Support ticket workflow: Legacy support ticket code exists outside V2. Not part of active V2 professor workflow.
- Direct Blackboard API integration: Not observed. CSV export is implemented as a browser-generated CSV download.

## 4. Architecture Evidence

- Frontend framework: Angular 18, from `facial-attendance/package.json` dependencies `@angular/*` version `^18.2.0`.
- Backend framework: FastAPI, from `requirements.txt` and `backend.py`.
- V2 backend routing: `v2/api.py` defines `APIRouter(prefix="/api/v2", tags=["V2 Attendance"])`; `backend.py` includes the V2 router.
- Database: V2 schema is PostgreSQL-oriented in `database/v2_schema.sql`; deployment uses `postgres:16-alpine` in `docker-compose.v2.yml`.
- Database compatibility layer: `services/db.py` supports Postgres via `DATABASE_URL` and SQLite fallback when `DATABASE_URL` is absent or explicitly SQLite.
- Recognition/embedding service: `services/face_embeddings.py` uses image/embedding logic for face profiles and recognition; dependencies include `opencv-python-headless`, `deepface`, `tf-keras`, `Pillow`, and `numpy`.
- Deployment-related files present: `docker-compose.v2.yml`, `Dockerfile.backend.v2`, `facial-attendance/Dockerfile.v2`, `facial-attendance/nginx.v2.conf`, `docker-compose.prod.yml`, `nginx/default.conf`, `.env.v2.example`, `.env`.
- Major V2 backend files: `v2/api.py`, `v2/service.py`, `v2/repository.py`, `v2/models.py`, `services/face_embeddings.py`.

## 5. Endpoint Evidence

### Authentication

- `POST /api/login` - implemented in `api/auth.py`, used by `LoginService`.
- `POST /login` - compatibility alias in `api/auth.py`.

### Professor Classes/Schedule

- `GET /api/v2/professors`
- `GET /api/v2/professors/{professor_id}/today/classes`
- `GET /api/v2/professors/{professor_id}/schedule`

### Class Roster

- `GET /api/v2/classes/{class_id}/students`
- `GET /api/v2/classes/{class_id}/students/{student_id}/history`

### Face Profile

- `GET /api/v2/classes/{class_id}/students/{student_id}/face-profile`
- `POST /api/v2/classes/{class_id}/students/{student_id}/face-profile`

### Recognition

- `POST /api/v2/classes/{class_id}/recognize`

### Session Lifecycle

- `POST /api/v2/classes/{class_id}/sessions/start`
- `GET /api/v2/sessions/{session_id}`
- `POST /api/v2/sessions/{session_id}/end`

### Attendance Events

- `POST /api/v2/sessions/{session_id}/events`
- `POST /api/v2/sessions/{session_id}/manual-attendance`

### Break Mode

- `POST /api/v2/sessions/{session_id}/break/start`
- `POST /api/v2/sessions/{session_id}/break/end`

### Review/Evidence/Finalization

- `GET /api/v2/sessions/{session_id}/review`
- `POST /api/v2/sessions/{session_id}/finalize`
- `POST /api/v2/sessions/{session_id}/students/{student_id}/confirm`

### Session History/Export

- `GET /api/v2/professors/{professor_id}/session-history`
- `GET /api/v2/classes/{class_id}/session-history`
- Blackboard-ready CSV export is generated in the Angular frontend from review/history data. No direct V2 backend CSV export endpoint or direct Blackboard API endpoint was observed.
