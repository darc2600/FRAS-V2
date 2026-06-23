# FRAS V2 - Facial Recognition Classroom Presence Monitoring

FRAS V2 is a professor-centered classroom presence monitoring system that uses facial recognition embeddings, session event tracking, professor review, and Blackboard-ready CSV export to support attendance validation for class sessions.

The original FRAS V1 system focused on general facial-recognition attendance checking and administrative workflows. V1 remains in the repository as historical background and legacy code. The final thesis and current implementation focus on FRAS V2.

## Final V2 Scope

FRAS V2 is designed around the professor's classroom workflow:

1. Login
2. Today's Classes
3. Class Roster
4. Face Profile Registration/Update
5. Live Session Monitoring
6. Manual Attendance
7. Facial Recognition Capture
8. Specific Student Break
9. Session Break
10. Return Detection Mode
11. Post-Session Review
12. Student Evidence
13. Professor Override
14. Mark Excused
15. Attendance Finalization
16. Session History
17. Blackboard-ready CSV Export

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, Python |
| Frontend | Angular / Ionic |
| Database | PostgreSQL for V2 deployment |
| Recognition | DeepFace, OpenCV, stored face embeddings |
| Deployment | Docker Compose, Nginx, PostgreSQL container |
| Dataset storage | Mounted `dataset/` directory for face profile images |

## Main V2 Source Areas

| Area | Path |
|---|---|
| V2 backend routes, models, service, repository | `v2/` |
| V2 database schema and seed/verification tools | `database/v2_schema.sql`, `database/*v2*` |
| V2 professor frontend pages | `facial-attendance/src/app/v2/pages/` |
| V2 frontend shared components | `facial-attendance/src/app/v2/components/` |
| Angular API wrapper | `facial-attendance/src/app/api.service.ts` |
| Face embedding helpers | `services/face_embeddings.py` |
| Docker Compose for V2 | `docker-compose.v2.yml` |
| Backend Dockerfile for V2 | `Dockerfile.backend.v2` |

## V2 API Overview

The V2 API is registered under:

```text
/api/v2
```

Representative endpoints:

| Workflow | Endpoint |
|---|---|
| Today's Classes | `GET /api/v2/professors/{professor_id}/today/classes` |
| Class Roster | `GET /api/v2/classes/{class_id}/students` |
| Face Profile | `GET/POST /api/v2/classes/{class_id}/students/{student_id}/face-profile` |
| Facial Recognition | `POST /api/v2/classes/{class_id}/recognize` |
| Start Session | `POST /api/v2/classes/{class_id}/sessions/start` |
| Session Detail | `GET /api/v2/sessions/{session_id}` |
| Events | `POST /api/v2/sessions/{session_id}/events` |
| Manual Attendance / Override | `POST /api/v2/sessions/{session_id}/manual-attendance` |
| Session Break | `POST /api/v2/sessions/{session_id}/break/start` |
| End Break | `POST /api/v2/sessions/{session_id}/break/end` |
| Review | `GET /api/v2/sessions/{session_id}/review` |
| Finalize | `POST /api/v2/sessions/{session_id}/finalize` |
| Session History | `GET /api/v2/professors/{professor_id}/session-history` |

Authentication is handled through:

```text
POST /api/login
```

## Blackboard-ready CSV Export

FRAS V2 generates Blackboard-ready CSV files in the frontend after attendance finalization.

Implementation source:

```text
facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts
```

This is a browser-side CSV download. It should not be described as direct Blackboard API synchronization.

## Running FRAS V2 with Docker

Prepare a V2 environment file from the example:

```bash
cp .env.v2.example .env
```

Start the V2 stack:

```bash
docker compose -f docker-compose.v2.yml up -d --build
```

Verify containers:

```bash
docker compose -f docker-compose.v2.yml ps
```

Open the frontend:

```text
http://localhost:8080
```

Open FastAPI docs:

```text
http://localhost:8000/docs
```

Important: database initialization and seed scripts can be destructive when run with reset/force flags. Use the V2 setup/runbook documentation before resetting V2 data.

## Documentation

| Document | Purpose |
|---|---|
| `docs/V2_WORKFLOW.md` | Final professor-centered V2 workflow |
| `docs/V2_DATABASE_DESIGN.md` | V2 database design |
| `docs/V2_DOCKER_DEPLOYMENT.md` | V2 Docker deployment guide |
| `docs/V2_LOCAL_SETUP.md` | Local V2 setup notes |
| `docs/FRAS_V2_USER_MANUAL.md` | Professor-facing V2 user manual |
| `docs/QA_TEST_PLAN.md` | V2 QA test plan |
| `docs/TEST_CASES.md` | V2 functional and negative test cases |
| `FRAS_V2_APPENDIX_D_API_DOCUMENTATION.md` | Appendix-ready V2 API documentation |
| `FRAS_V2_APPENDIX_M_PROJECT_TIMELINE.md` | Appendix-ready project timeline and Git activity |
| `FRAS_V2_APPENDICES_EVIDENCE.md` | Appendix evidence package |

## Testing Evidence

The safe recognition decision unit test can be run with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_v2_recognition_decision.py -q
```

Some integration scripts reset, seed, or write database/session data. Inspect them before running on a thesis/demo database.

## Repository Notes

- Keep V1 references as historical background only.
- Use `v2/`, `database/v2_schema.sql`, and `facial-attendance/src/app/v2/` for final V2 evidence.
- Do not commit deployment archives, database dumps, `.env` files, passwords, JWT secrets, SSH credentials, or private keys.
- Large deployment archives should stay outside Git or be handled with an approved artifact process.

## Current Status

FRAS V2 is the final thesis implementation in this repository. It supports the professor-centered presence monitoring lifecycle from class selection through finalized attendance review and Blackboard-ready CSV export.
