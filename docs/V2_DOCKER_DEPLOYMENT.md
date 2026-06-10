# FRAS V2 Docker Deployment

This guide runs the instructor-only FRAS V2 stack with Docker Compose.

The V2 stack uses:

- PostgreSQL database container
- FastAPI backend container
- Angular/Nginx frontend container

The containers do not reset or seed the database automatically. Schema initialization, seeding, and cleanup are manual commands so deployment data is not deleted by accident.

## 1. Prerequisites

Install and start Docker Desktop locally, or Docker Engine on the VPS.

For local testing on Windows, Docker Desktop must be open before running `docker compose` commands.

## 2. Files

V2 Docker files:

```text
Dockerfile.backend.v2
docker-compose.v2.yml
.env.v2.example
facial-attendance/Dockerfile.v2
facial-attendance/nginx.v2.conf
```

The older Docker files are left untouched.

## 3. Create `.env`

If you already have a local `.env`, back it up first:

```powershell
Copy-Item .env .env.local.backup
```

Then copy the V2 example:

```powershell
Copy-Item .env.v2.example .env
```

Update values before deployment:

```text
POSTGRES_USER=fras_v2
POSTGRES_PASSWORD=change-this-v2-password
POSTGRES_DB=fras_v2
TZ=Asia/Manila

DATABASE_URL=postgresql://fras_v2:change-this-v2-password@db:5432/fras_v2
JWT_SECRET=replace-with-a-long-random-secret
FRAS_MODE=v2
DATASET_PATH=/app/dataset
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

For VPS deployment, set `CORS_ORIGINS` to the real domain origin.

The V2 compose file also uses `TZ=Asia/Manila` and starts PostgreSQL with `timezone=Asia/Manila` so attendance timestamps match Philippine time.

## 4. Faculty Load DOCX

For seeding, place the faculty load document here:

```text
deployment/seed/FRAS-prof-database.docx
```

If the folder does not exist:

```powershell
New-Item -ItemType Directory -Force deployment\seed
```

Then copy the file:

```powershell
Copy-Item "C:\Users\YourName\Downloads\FRAS REVISIONS\FRAS-prof-database.docx" deployment\seed\FRAS-prof-database.docx
```

The Docker Compose file mounts `deployment/seed` into the backend container as read-only.

## 5. Build and Start

```powershell
docker compose -f docker-compose.v2.yml up -d --build
```

Check container status:

```powershell
docker compose -f docker-compose.v2.yml ps
```

View logs:

```powershell
docker compose -f docker-compose.v2.yml logs -f backend
```

Open the frontend:

```text
http://localhost:8080
```

Backend docs:

```text
http://localhost:8000/docs
```

## 6. Initialize Database

Run this only for a fresh deployment database or an intentional reset:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/init_v2_database.py --force
```

This is destructive for V2 tables.

## 7. Seed Data

Seed professors, schedules, courses, rooms, sample students, enrollments, and the test professor:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/seed_v2_integration_data.py --docx /app/deployment/seed/FRAS-prof-database.docx --enroll-all-active-classes
```

The seed command is additive unless `--replace-docx-schedules` is used.

## 8. Clean Deployment/Demo Data

Clear face profiles, embeddings, and saved V2 face image files:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_face_data.py --force
```

Clear session history/activity:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/clear_v2_session_data.py --force
```

These cleanup commands do not delete professors, classes, students, or enrollments.

## 9. Verify Data

Check table list:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/check_v2_database.py
```

Verify professor/class/student seed:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/verify_v2_integration_seed.py
```

Verify roster size and duplicates:

```powershell
docker compose -f docker-compose.v2.yml exec backend python database/check_v2_roster_counts.py
```

Expected deployment-prep roster state:

- 40 managed sample students
- no duplicate student numbers
- no duplicate enrollments
- 40 managed sample students enrolled in every active non-online class

## 10. Test Accounts

Development/demo accounts:

| Account | Email | Password |
| --- | --- | --- |
| Test professor | `test.professor@fras.local` | `password123` |
| Faculty professors | generated from faculty load document | `password` |

## 11. V2-Only Backend Mode

The backend container uses:

```text
FRAS_MODE=v2
```

This loads the auth router and V2 router, while skipping legacy/admin/V1 router imports.

It does not delete old files. To restore full legacy router loading:

```text
FRAS_MODE=full
```

## 12. Production Notes

For camera access on a real VPS/domain, use HTTPS. Browsers generally block camera access on non-localhost HTTP origins.

Verify Philippine time after deployment:

```powershell
docker compose -f docker-compose.v2.yml exec backend date
docker compose -f docker-compose.v2.yml exec db date
docker compose -f docker-compose.v2.yml exec db psql -U fras_v2 -d fras_v2 -c "SHOW timezone;"
```

For production-like deployment:

- use a strong `JWT_SECRET`
- use a strong PostgreSQL password
- keep PostgreSQL port private if possible
- back up the PostgreSQL volume before resets
- back up `dataset/` if real face profiles are registered
- do not run `init_v2_database.py --force` unless intentionally resetting V2

## 13. Stop Containers

```powershell
docker compose -f docker-compose.v2.yml down
```

Stop and remove containers plus the PostgreSQL named volume:

```powershell
docker compose -f docker-compose.v2.yml down -v
```

`down -v` deletes the database volume. Use it only when you intentionally want a fresh database.
