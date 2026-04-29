# FRAS Deployment Guide

This guide is for the cleaned Docker-based deployment flow.

## What this deployment uses

- FastAPI backend served by Uvicorn on port `8000`
- Angular frontend served by Nginx on port `8080`
- Nginx proxy for `/api/*` requests from the frontend to the backend
- SQLite demo database mounted from `./attendance.db`
- Local dataset folder mounted from `./dataset`

## First-time setup

```bash
cp .env.example .env
python scripts/generate_secret.py
```

Paste the generated value into `.env`:

```env
JWT_SECRET=your-generated-secret-here
```

The default demo database config is:

```env
DATABASE_URL=sqlite:////app/attendance.db
SQLITE_DB_PATH=/app/attendance.db
DATASET_PATH=/app/dataset
```

## Build the Angular frontend

Run this from the project root:

```bash
cd facial-attendance
npm install
npm run build
cd ..
```

The Docker frontend service expects the Angular build output at:

```txt
facial-attendance/dist/facial-attendance
```

## Check deployment config

```bash
python scripts/check_deployment_config.py
```

## Start production containers

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Open:

```txt
http://localhost:8080
```

Backend API docs:

```txt
http://localhost:8080/docs
```

## Stop containers

```bash
docker compose -f docker-compose.prod.yml down
```

## View logs

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

## Important notes

Do not commit `.env`.

Do not write real server passwords or database passwords in markdown files.

For the thesis/demo branch, SQLite is the official database mode. PostgreSQL can be re-enabled later after schema migration and seed data are finalized.
