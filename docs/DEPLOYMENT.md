# FRAS Deployment Notes

This document defines the deployment direction for the current branch.

## Current Recommended Demo Deployment Strategy

Use one official path at a time.

For the current cleanup branch, the recommended demo path is:

```txt
FastAPI backend + Angular build + SQLite demo database
```

PostgreSQL support exists, but it should be treated as an optional production path until the database workflow is fully stabilized.

---

## Environment Variables

Create a real `.env` file from `.env.example` when deploying.

Never place real passwords, SSH credentials, database passwords, or JWT secrets inside README files, feedback documents, screenshots, or committed docs.

Recommended environment variables:

```env
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///attendance.db
DATASET_PATH=dataset
FRAS_ENV=production
```

---

## SQLite Demo Deployment

SQLite is easiest for a controlled thesis demonstration.

Benefits:

- Simple to copy and back up
- No database server required
- Easy to reset for demo
- Lower deployment complexity

Risks:

- Not ideal for multi-server production
- Requires careful file backup
- Concurrent write behavior is limited compared to PostgreSQL

---

## PostgreSQL Production Path

PostgreSQL should be used only after the schema and migration workflow are finalized.

Before switching to PostgreSQL, confirm:

- All tables exist in PostgreSQL
- Face data paths remain valid
- Demo data can be seeded again
- Backups are working
- The frontend/backend are using the same deployed API path

---

## Docker Notes

The repository includes Docker-related files, but Docker should be finalized in a dedicated patch.

Before relying on Docker in production, verify:

- `Dockerfile` is valid UTF-8 text
- `.env` is present on the server but not committed
- volumes are mapped correctly
- dataset storage is persistent
- database storage is persistent
- frontend build output exists before serving with Nginx

---

## Deployment Safety Checklist

Before a live demo:

- [ ] Backend starts successfully
- [ ] Frontend loads successfully
- [ ] Login works
- [ ] Student list loads
- [ ] Attendance logs load
- [ ] Reports page loads
- [ ] Room schedule loads
- [ ] Support ticket page loads
- [ ] Analytics page loads
- [ ] `dataset/` exists and is readable/writable
- [ ] `attendance.db` exists and is backed up
- [ ] No real credentials are committed
