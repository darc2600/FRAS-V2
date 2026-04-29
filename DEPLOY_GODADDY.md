# GoDaddy Deployment Notes

This repo appears to be deployed on a GoDaddy-hosted VPS, not simple shared hosting.

## What the repo shows

- Backend is a Dockerized FastAPI app.
  - `Dockerfile` runs `uvicorn backend:app --host 0.0.0.0 --port 8000`
  - `docker-compose.prod.yml` defines a `backend` service on port `8000`
- Frontend is an Angular static build.
  - `facial-attendance/angular.json` outputs to `dist/facial-attendance`
  - `facial-attendance/package.json` builds with `ng build`
  - `docker-compose.prod.yml` mounts `./facial-attendance/dist/facial-attendance` into nginx
- The deployment host looks like a Linux VPS.
  - `docker-compose.prod.yml` bind-mounts `/home/frasijbmapua/FRAS/dataset:/app/dataset:rw`
  - `CHANGELOG.md` says fixes were "copied into the running container and validated on the VPS"

## Important implications

- The frontend is built for same-origin API calls.
  - `facial-attendance/src/app/api.service.ts` uses `backendUrl = ''`
  - `facial-attendance/src/app/login/login.service.ts` calls `/api/login`
- That means the live host needs to serve the Angular app and also route `/api/*` to the backend container.
- The current backend CORS config in `backend.py` only allows localhost dev origins, so production likely relies on same-origin reverse proxying.

## Current local state

- Uncommitted backend change:
  - `backend.py` adds the repo root to `sys.path` near the top of the file
- Fresh frontend production build was generated on `2026-04-28`
- A deployable frontend zip was created:
  - `deploy_frontend_browser_20260428.zip`
- The older `deploy_frontend.zip` is not the correct static deployment artifact. It contains the frontend source tree, not only the built browser files.

## Recommended deployment flow

### Frontend

Use the newly built browser files from:

- `facial-attendance/dist/facial-attendance/browser`

Or upload:

- `deploy_frontend_browser_20260428.zip`

If deploying through GoDaddy file manager or SFTP, extract the zip into the document root used by the site, or into the directory your nginx/apache config serves for the frontend.

### Backend

The repo indicates two likely ways the backend has been updated before:

1. Copy changed files into the running container
2. Rebuild and restart the backend container with Docker Compose

If the server is using this repo layout directly, the safest long-term path is:

1. Upload the updated repo files
2. Rebuild the backend image
3. Restart the backend service

If the team has been hot-patching live containers, then the changed `backend.py` also needs to be copied into the running container and the backend process/container restarted.

## Server pieces to verify on GoDaddy

- The frontend web root points at the built Angular files
- `/api/*` is reverse-proxied to the backend on port `8000`
- `DATABASE_URL` is present for Postgres if production is using Postgres
- The dataset mount path exists on the VPS:
  - `/home/frasijbmapua/FRAS/dataset`

## Suggested command flow on the VPS

From the app directory on the server:

```bash
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

If the frontend is also served by the compose nginx service:

```bash
docker compose -f docker-compose.prod.yml up -d frontend
```

If the frontend is served outside Docker by GoDaddy/nginx/apache, upload the contents of:

```text
facial-attendance/dist/facial-attendance/browser
```

instead of restarting the compose `frontend` service.
