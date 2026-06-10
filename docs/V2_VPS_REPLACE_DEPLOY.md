# FRAS V2 VPS Replace Deploy

Use this when you want to replace what is currently running on the VPS with the V2 Docker stack.

## 1) Copy/Update Code On VPS

From your VPS project directory:

```bash
git pull --ff-only
```

If you deploy from a zip/tar upload, extract into the same VPS app directory and ensure these files exist:

- `docker-compose.v2.yml`
- `Dockerfile.backend.v2`
- `facial-attendance/Dockerfile.v2`
- `deployment/v2_vps_redeploy.sh`

## 2) Prepare V2 Environment

```bash
cp -n .env.v2.example .env
nano .env
```

Set at least:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `JWT_SECRET`
- `FRAS_MODE=v2`
- `CORS_ORIGINS` for your real domain/IP

## 3) Replace Existing Deployment (Keep DB)

This removes old app containers (including the old `docker-compose.prod.yml` stack when present) and starts V2, but keeps PostgreSQL data volume:

```bash
bash deployment/v2_vps_redeploy.sh
```

## 4) Full Clean Replace (Delete DB Too)

This removes containers and V2 DB volume, then starts from empty DB:

```bash
WIPE_DB=1 bash deployment/v2_vps_redeploy.sh
```

Then initialize/seed:

```bash
docker compose -f docker-compose.v2.yml exec backend python database/init_v2_database.py --force
docker compose -f docker-compose.v2.yml exec backend python database/seed_v2_integration_data.py --docx /app/deployment/seed/FRAS-prof-database.docx --enroll-all-active-classes
```

## 5) Verify

```bash
docker compose -f docker-compose.v2.yml ps
docker compose -f docker-compose.v2.yml logs --tail=100 backend
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8000/docs
```

## Notes

- `WIPE_DB=1` is destructive and deletes V2 PostgreSQL volume data.
- The script attempts a best-effort SQL backup into `deployment/backups/` before stopping services.
- For browser camera access on domain deployments, use HTTPS.
- If your old stack uses a different compose filename, pass it as `OLD_COMPOSE_FILE`, for example: `OLD_COMPOSE_FILE=docker-compose.old.yml bash deployment/v2_vps_redeploy.sh`.
