# FRAS GoDaddy VPS Deployment

This deployment path is for a GoDaddy Linux VPS using Docker Compose, PostgreSQL, the FastAPI backend, and nginx serving the Angular frontend.

## What Changed

- Production now uses PostgreSQL instead of SQLite.
- `docker-compose.prod.yml` starts a `db` service, waits for it before starting the backend, and stores data in the `postgres_data` Docker volume.
- The frontend nginx container now serves `facial-attendance/dist/facial-attendance/browser`, which is the real Angular browser output folder.
- Mapua image paths are root-relative (`/assets/...`) so Linux/nginx serves them consistently.

## 1. Prepare `.env`

On the VPS, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Use strong values:

```env
FRAS_ENV=production
JWT_SECRET=replace-with-a-long-random-secret
JWT_EXPIRE_MINUTES=1440

POSTGRES_USER=fras_user
POSTGRES_PASSWORD=replace-with-a-strong-postgres-password
POSTGRES_DB=frasdb
DATABASE_URL=postgresql://fras_user:replace-with-a-strong-postgres-password@db:5432/frasdb

DATASET_PATH=/app/dataset
CORS_ORIGINS=https://your-domain.example,http://your-server-ip:8080
```

The password in `DATABASE_URL` must match `POSTGRES_PASSWORD`.

## 2. Build The Frontend

From the repo root:

```bash
cd facial-attendance
npm ci
npm run build
cd ..
```

The important output folder is:

```text
facial-attendance/dist/facial-attendance/browser
```

That folder must contain `index.html` and `assets/mapua-logo.png`, `assets/mapua-bg.jpg`, and `assets/mapua-bg2.jpg`.

## 3. Start PostgreSQL

```bash
docker compose -f docker-compose.prod.yml up -d db
```

Check it:

```bash
docker compose -f docker-compose.prod.yml ps
```

## 4. Migrate SQLite Data To PostgreSQL

Run this once after the cleaned `attendance.db` is in the repo root on the VPS:

```bash
docker compose -f docker-compose.prod.yml --profile tools run --rm --build migrate
```

This uses:

```text
scripts/migrate_sqlite_to_postgres.py
```

It creates the PostgreSQL schema, imports the cleaned capstone data, and resets identity sequences so new records continue at the correct IDs.

## 5. Start The App

```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

Open:

```text
http://your-server-ip:8080
```

If your domain points to the VPS through another nginx/apache reverse proxy, point it to `http://127.0.0.1:8080`.

## 6. Verify

Check containers:

```bash
docker compose -f docker-compose.prod.yml ps
```

Check backend logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

Check the API:

```bash
curl -I http://127.0.0.1:8080/docs
```

Check frontend assets:

```bash
curl -I http://127.0.0.1:8080/assets/mapua-logo.png
curl -I http://127.0.0.1:8080/assets/mapua-bg2.jpg
```

Both asset checks should return `HTTP/1.1 200 OK`.

## Login Accounts

The cleaned presentation database keeps these main accounts:

```text
admin@mapua.edu.ph       / admin123
superadmin@fras.com      / super123
jane.smith@mapua.edu.ph  / password123
```

The other instructor accounts from the workbook are also retained with `password123`.

## Common Fixes

If the login background or sidebar logo is missing:

```bash
ls -la facial-attendance/dist/facial-attendance/browser/assets
```

Make sure nginx is serving the `browser` folder, not the parent `dist/facial-attendance` folder.

If PostgreSQL connection fails:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 db
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

Confirm `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` match in `.env`.

If the VPS already has another service on port `8080`, change the frontend port mapping in `docker-compose.prod.yml`:

```yaml
ports:
  - "8081:80"
```

Then open `http://your-server-ip:8081`.
