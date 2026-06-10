# FRAS V2 Containerization Runbook

This runbook documents the practical process for moving FRAS V2 from local code to Docker containers, then initializing, seeding, cleaning, and verifying the Docker database.

Use this when preparing a local Docker demo or a VPS deployment rehearsal.

## 1. What Gets Containerized

FRAS V2 uses three containers:

| Container | Purpose |
|---|---|
| `frontend` | Angular/Ionic app built with Node and served by Nginx |
| `backend` | FastAPI backend running `backend:app` through Uvicorn |
| `db` | PostgreSQL database with persistent Docker volume |

The V2 Docker files are separate from older deployment files:

```text
Dockerfile.backend.v2
docker-compose.v2.yml
.env.v2.example
facial-attendance/Dockerfile.v2
facial-attendance/nginx.v2.conf
```

## 2. Important Separation Notes

The Docker PostgreSQL database is separate from your local PostgreSQL database.

Local PostgreSQL may use:

```text
localhost:5432/fras_v2
```

Docker uses the database service name inside the container network:

```text
postgresql://fras_v2:<password>@db:5432/fras_v2
```

Docker also creates its own persistent database volume:

```text
fras_fras_v2_postgres_data
```

That means a successful local seed does not automatically appear inside Docker. You must initialize and seed the Docker database separately.

## 3. Prepare Environment File

Back up your existing local `.env` first if it has local PostgreSQL credentials:

```powershell
Copy-Item .env .env.local.backup
```

Copy the V2 Docker example:

```powershell
Copy-Item .env.v2.example .env
```

Minimum expected `.env` values:

```text
POSTGRES_USER=fras_v2
POSTGRES_PASSWORD=change-this-v2-password
POSTGRES_DB=fras_v2
POSTGRES_PORT=5432
TZ=Asia/Manila

DATABASE_URL=postgresql://fras_v2:change-this-v2-password@db:5432/fras_v2
JWT_SECRET=replace-with-a-long-random-secret
JWT_EXPIRE_MINUTES=1440
FRAS_MODE=v2
DATASET_PATH=/app/dataset
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

BACKEND_PORT=8000
FRONTEND_PORT=8080
```

For VPS deployment, update `CORS_ORIGINS` to the real HTTPS domain.

`TZ=Asia/Manila` keeps backend timestamps, container dates, and PostgreSQL session time aligned with Philippine time.

## 4. Prepare Faculty Load Document

Create the seed folder if needed:

```powershell
New-Item -ItemType Directory -Force deployment\seed
```

Copy the faculty load document:

```powershell
Copy-Item "C:\Users\sugz1\Downloads\FRAS REVISIONS\FRAS-prof-database.docx" deployment\seed\FRAS-prof-database.docx
```

Inside the backend container, this file is mounted as:

```text
/app/deployment/seed/FRAS-prof-database.docx
```

## 5. Build and Start Containers

Docker Desktop must be open on Windows before running this.

Build and start:

```powershell
docker compose -f docker-compose.v2.yml up -d --build
```

Check status:

```powershell
docker compose -f docker-compose.v2.yml ps
```

Expected:

```text
fras-db-1        healthy
fras-backend-1   healthy
fras-frontend-1  started
```

Open the app:

```text
http://localhost:8080
```

Open backend docs:

```text
http://localhost:8000/docs
```

## 6. Initialize Docker Database

Run this for a new Docker database volume:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/init_v2_database.py --force
```

Warning: `--force` is destructive for V2 tables in the Docker database.

It is required for a fresh database, but do not run it casually after real data exists.

## 7. Seed Docker Database

Seed professors, courses, rooms, classes, test professor, sample students, and enrollments:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/seed_v2_integration_data.py --docx /app/deployment/seed/FRAS-prof-database.docx --enroll-all-active-classes
```

This is additive by default.

Expected seed behavior:

- imports professor schedules from the DOCX
- creates professor login accounts
- creates course records
- creates room records
- creates class records
- creates 40 managed sample students
- enrolls the 40 managed sample students into active non-online classes
- creates the special test professor account

## 8. Clean Demo State

After QA or before a clean demo, clear face data:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_face_data.py --force
```

Clear session history/activity:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_session_data.py --force
```

These cleanup scripts do not delete:

- users
- professors
- courses
- rooms
- classes
- schedules
- students
- enrollments

## 9. Verify Docker Database

Check V2 tables:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/check_v2_database.py
```

Verify seeded professor/class/student data:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/verify_v2_integration_seed.py
```

Verify roster size and duplicates:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/check_v2_roster_counts.py
```

Expected clean roster state:

```text
managed sample students: 40
duplicate student numbers: none
duplicate enrollments: none
active sample enrollments = expected enrollments
```

## 10. Login Test

Open:

```text
http://localhost:8080
```

Use:

```text
Email: test.professor@fras.local
Password: password123
```

Expected:

- login succeeds
- app opens Classes page
- test professor schedule appears
- class roster loads students
- Session History is empty after cleanup
- Face Profile statuses show no registered face data after cleanup

## 10.1. Timezone Check

After starting the stack, verify that the VPS containers are using Philippine time:

```powershell
docker compose -f docker-compose.v2.yml exec backend date
docker compose -f docker-compose.v2.yml exec db date
docker compose -f docker-compose.v2.yml exec db psql -U fras_v2 -d fras_v2 -c "SHOW timezone;"
```

Expected PostgreSQL timezone:

```text
Asia/Manila
```

## 11. Recommended Demo Flow

For a clean demo or panel test:

1. Login as `test.professor@fras.local`.
2. Open Classes.
3. Pick one current class for the normal attendance flow.
4. Register/update face data for a few sample students.
5. Start Monitor.
6. Test Manual Capture or Auto Capture.
7. Test Manual Attendance.
8. End Session.
9. Review attendance.
10. Override or accept selected student records.
11. Finalize Attendance.
12. Export CSV.
13. Open Session History.

For edge testing, use a second test professor class:

- late arrival
- very late arrival
- session break
- return detection mode
- excused/override status

## 12. Why 40 Students Are Enrolled Across Classes

Use this explanation for panelists:

> Since official registrar enrollment data is not yet integrated, FRAS V2 uses a controlled integration-testing roster of 40 sample students. These students are enrolled into active non-online classes so each professor schedule can be tested with a realistic Mapua class size. This allows the team to validate face registration, live monitoring, session review, finalization, and CSV export consistently. In production, actual enrollments would come from the registrar, SIS, Blackboard, or an official class list import.

## 13. Common Commands

View logs:

```powershell
docker compose -f docker-compose.v2.yml logs -f backend
```

Restart backend:

```powershell
docker compose -f docker-compose.v2.yml restart backend
```

Rebuild after code changes:

```powershell
docker compose -f docker-compose.v2.yml up -d --build
```

Stop containers:

```powershell
docker compose -f docker-compose.v2.yml down
```

Stop containers and delete Docker database volume:

```powershell
docker compose -f docker-compose.v2.yml down -v
```

Warning: `down -v` deletes the Docker PostgreSQL data volume.

## 14. Common Issues

### Docker Build Fails on Google Fonts

Cause:

Angular production build tried to fetch external Google Fonts during Docker build.

Fix already applied:

- removed external Roboto import from `src/styles.css`
- set Angular production `optimization.fonts` to `false`

### Containers Start But Login Fails

Likely cause:

Docker database has not been initialized or seeded.

Run:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/init_v2_database.py --force
docker compose -f docker-compose.v2.yml exec backend python database/seed_v2_integration_data.py --docx /app/deployment/seed/FRAS-prof-database.docx --enroll-all-active-classes
```

### Session History Has Old QA Records

Run:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_session_data.py --force
```

### Face Data Still Appears Registered

Run:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_face_data.py --force
```

### Camera Does Not Work on VPS

Browsers usually require HTTPS for camera access outside localhost.

Localhost works with HTTP:

```text
http://localhost:8080
```

VPS/domain deployments should use HTTPS.

## 15. Deployment Principle

Do not make containers auto-reset, auto-seed, or auto-clean the database on startup.

Manual commands are safer because they prevent accidental deletion of real attendance, face profiles, or seeded professor schedules.
