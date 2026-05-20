# Appendix H: Deployment and Environment Configuration

## H.1 Overview

This appendix documents the deployment and environment configuration of the Facial Recognition Attendance System (FRAS). The documented production deployment is based on the repository's available Docker Compose configuration and uses the following components:

- Docker Compose for container orchestration.
- FastAPI served by Uvicorn for the backend API.
- Angular/Ionic for the frontend application.
- PostgreSQL as the production database.
- Nginx for serving the frontend and proxying API requests.

The primary production configuration file is:

```text
docker-compose.prod.yml
```

The backend container is built from:

```text
Dockerfile
```

The Nginx configuration used by the frontend container is:

```text
nginx/default.conf
```

Additional VPS-oriented Nginx and systemd files are available under `deployment/`, but the Docker Compose deployment is the main documented workflow for the current production stack.

## H.2 Production Architecture

The production environment is composed of three main runtime services and one optional migration service.

| Service | Technology | Purpose | Port exposure |
|---|---|---|---|
| `db` | PostgreSQL 16 Alpine | Stores production application data. | `127.0.0.1:5432:5432` |
| `backend` | FastAPI, Uvicorn, Python 3.11 | Provides API endpoints for authentication, attendance, recognition, registration, administration, and reports. | `127.0.0.1:8000:8000` |
| `frontend` | Nginx stable Alpine | Serves the Angular/Ionic build and proxies API requests to the backend. | `8080:80` |
| `migrate` | Python backend image | Optional one-time SQLite-to-PostgreSQL migration tool. | Not exposed |

The production request flow is as follows:

1. The user accesses the web application through the Nginx frontend service on port `8080`.
2. Nginx serves static Angular/Ionic files from the compiled frontend build directory.
3. Requests beginning with `/api/` are proxied by Nginx to the backend service at `http://backend:8000`.
4. The FastAPI backend processes business logic, face recognition, authentication, attendance recording, reporting, and administrative requests.
5. The backend connects to the PostgreSQL database through the `DATABASE_URL` environment variable.
6. Face image data and application data directories are mounted into the backend container for persistent access.

The simplified production architecture is:

```text
Browser
   |
   v
Nginx Frontend Container :8080
   |-- serves Angular/Ionic static files
   |
   |-- /api/*, /docs, /openapi.json
       v
FastAPI Backend Container :8000
       |
       v
PostgreSQL Database Container :5432
```

## H.3 Environment Requirements

The following environment requirements are based on the available repository configuration.

| Requirement | Description |
|---|---|
| Operating system | Linux VPS or local machine capable of running Docker. |
| Docker | Required to build and run the backend, database, and frontend containers. |
| Docker Compose | Required to run `docker-compose.prod.yml`. |
| Node.js and npm | Required to install dependencies and build the Angular/Ionic frontend before running the frontend container. |
| Python 3.11 | Used inside the backend Docker image. Local Python is useful for helper scripts such as secret generation. |
| PostgreSQL | Provided through the Docker Compose `db` service using `postgres:16-alpine`. |
| Nginx | Provided through the Docker Compose `frontend` service using `nginx:stable-alpine`. |

The backend image installs runtime libraries for OpenCV and image processing, including libraries required by face recognition and image handling packages.

## H.4 Environment Variables

The production deployment uses a `.env` file loaded by Docker Compose. The repository provides `.env.example` as a template.

Required and relevant environment variables include:

| Variable | Purpose |
|---|---|
| `FRAS_ENV` | Identifies the runtime environment, typically `production`. |
| `JWT_SECRET` | Secret key used to sign JWT authentication tokens. |
| `JWT_EXPIRE_MINUTES` | Token expiration duration in minutes. |
| `POSTGRES_USER` | PostgreSQL username. |
| `POSTGRES_PASSWORD` | PostgreSQL password. |
| `POSTGRES_DB` | PostgreSQL database name. |
| `DATABASE_URL` | Backend database connection string. |
| `DATASET_PATH` | Container path for face image dataset storage. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. |

Sample `.env` configuration:

```env
FRAS_ENV=production
JWT_SECRET=replace-this-with-a-long-random-secret
JWT_EXPIRE_MINUTES=1440

POSTGRES_USER=fras_user
POSTGRES_PASSWORD=replace-this-with-a-strong-postgres-password
POSTGRES_DB=frasdb
DATABASE_URL=postgresql://fras_user:replace-this-with-a-strong-postgres-password@db:5432/frasdb

DATASET_PATH=/app/dataset
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,https://your-domain.example
```

The PostgreSQL password in `DATABASE_URL` must match `POSTGRES_PASSWORD`.

## H.5 Installation Steps

### H.5.1 Prepare the Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the file and replace placeholder values:

```bash
nano .env
```

For the JWT secret, the repository includes a helper script:

```bash
python scripts/generate_secret.py
```

The generated value should be placed in `JWT_SECRET`.

### H.5.2 Install and Build the Frontend

From the repository root, install frontend dependencies and build the Angular/Ionic application:

```bash
cd facial-attendance
npm ci
npm run build
cd ..
```

The production Compose file expects the browser build output at:

```text
facial-attendance/dist/facial-attendance/browser
```

This directory should contain `index.html` and the required static assets.

### H.5.3 Start PostgreSQL

Start the database container:

```bash
docker compose -f docker-compose.prod.yml up -d db
```

Check the service status:

```bash
docker compose -f docker-compose.prod.yml ps
```

### H.5.4 Optional Data Migration

If deploying from an existing SQLite `attendance.db`, the repository provides a migration service profile. This step is intended to be run once after the SQLite database is available in the repository root.

```bash
docker compose -f docker-compose.prod.yml --profile tools run --rm --build migrate
```

The migration command uses:

```text
scripts/migrate_sqlite_to_postgres.py
```

This migration service imports data into PostgreSQL and resets identity sequences for continued production use.

### H.5.5 Start the Backend and Frontend

Build and start the backend and frontend services:

```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

Open the deployed application:

```text
http://your-server-ip:8080
```

The backend OpenAPI documentation is available through the frontend Nginx proxy:

```text
http://your-server-ip:8080/docs
```

The raw OpenAPI JSON is available at:

```text
http://your-server-ip:8080/openapi.json
```

## H.6 Deployment Workflow

The recommended deployment workflow is:

1. Pull or upload the latest FRAS source code to the server.
2. Prepare the `.env` file using `.env.example`.
3. Build the Angular/Ionic frontend with `npm ci` and `npm run build`.
4. Start the PostgreSQL service and verify that it is healthy.
5. Run the optional migration service if existing SQLite data must be imported.
6. Build and start the FastAPI backend and Nginx frontend services.
7. Verify the frontend, API documentation, and static assets.
8. Review backend, frontend, and database logs for errors.

Sample full deployment command sequence:

```bash
cp .env.example .env
nano .env

cd facial-attendance
npm ci
npm run build
cd ..

docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml --profile tools run --rm --build migrate
docker compose -f docker-compose.prod.yml up -d --build backend frontend
docker compose -f docker-compose.prod.yml ps
```

If no SQLite-to-PostgreSQL migration is required, the migration command may be omitted.

## H.7 Sample Docker Commands

Start all production services:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Start only the database:

```bash
docker compose -f docker-compose.prod.yml up -d db
```

Start only backend and frontend services:

```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

View all service status:

```bash
docker compose -f docker-compose.prod.yml ps
```

View backend logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

Follow backend logs:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

View frontend logs:

```bash
docker compose -f docker-compose.prod.yml logs -f frontend
```

View database logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 db
```

Run the migration tool:

```bash
docker compose -f docker-compose.prod.yml --profile tools run --rm --build migrate
```

Restart services:

```bash
docker compose -f docker-compose.prod.yml restart backend frontend
```

Stop containers:

```bash
docker compose -f docker-compose.prod.yml down
```

Stop containers while keeping the PostgreSQL volume:

```bash
docker compose -f docker-compose.prod.yml down
```

Stop containers and remove the PostgreSQL volume:

```bash
docker compose -f docker-compose.prod.yml down -v
```

The `down -v` command removes the `postgres_data` volume and should only be used when intentionally deleting the database.

## H.8 Nginx Configuration

The Docker frontend service mounts:

```text
nginx/default.conf
```

This configuration:

- serves Angular/Ionic static files from `/usr/share/nginx/html`;
- uses `try_files` to support Angular single-page application routing;
- proxies `/api/` requests to the backend container;
- proxies `/docs` to the FastAPI Swagger UI;
- proxies `/openapi.json` to the FastAPI OpenAPI schema;
- allows request bodies up to `30M`, which supports image upload operations.

Relevant Nginx routing behavior:

```text
/api/*        -> http://backend:8000/api/*
/docs         -> http://backend:8000/docs
/openapi.json -> http://backend:8000/openapi.json
/*            -> Angular/Ionic index.html fallback
```

The repository also includes `deployment/nginx_fras.conf` for a non-container or VPS reverse-proxy setup. That file serves the frontend from `/var/www/fras/browser` and proxies `/api/` requests to a FastAPI backend running on `127.0.0.1:8000`.

## H.9 Verification Steps

After deployment, verify that the containers are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

Verify the API documentation page:

```bash
curl -I http://127.0.0.1:8080/docs
```

Verify the OpenAPI schema:

```bash
curl -I http://127.0.0.1:8080/openapi.json
```

Verify frontend static assets:

```bash
curl -I http://127.0.0.1:8080/assets/mapua-logo.png
curl -I http://127.0.0.1:8080/assets/mapua-bg2.jpg
```

Check backend logs if API requests fail:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

Check database logs if the backend cannot connect to PostgreSQL:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 db
```

## H.10 Deployment Files Available in the Repository

| File | Purpose |
|---|---|
| `docker-compose.prod.yml` | Defines PostgreSQL, FastAPI backend, Nginx frontend, and migration services. |
| `Dockerfile` | Builds the Python 3.11 FastAPI backend image with required image-processing libraries. |
| `.env.example` | Template for required production environment variables. |
| `nginx/default.conf` | Nginx configuration used by the frontend container. |
| `deployment/nginx_fras.conf` | Optional VPS Nginx site configuration for non-container frontend serving. |
| `deployment/fras-backend.service` | Optional systemd unit for running Uvicorn directly on a VPS. |
| `deployment/fras_env.example` | Example environment file for the optional systemd deployment. |
| `scripts/migrate_sqlite_to_postgres.py` | Migration script used by the Docker Compose `migrate` profile. |
| `scripts/check_deployment_config.py` | Helper script for checking deployment configuration. |
| `scripts/generate_secret.py` | Helper script for generating a JWT secret. |

## H.11 Limitations and Not Applicable Items

The following items are not documented as active production requirements because they are not part of the current Docker Compose production path:

| Item | Finding |
|---|---|
| Kubernetes deployment | No Kubernetes manifests were found in the repository. |
| Cloud object storage as the required dataset backend | S3 utility code exists, but the production Compose file mounts `./dataset` into `/app/dataset`. |
| HTTPS termination inside the Compose stack | The provided container Nginx configuration listens on HTTP port 80. TLS may be added through an external reverse proxy or VPS-level Nginx/Certbot setup. |
| Horizontal backend scaling | The Compose file runs one backend service definition and does not configure multiple replicas. |
| CI/CD pipeline deployment commands | GitHub workflow files exist, but no complete automated production release pipeline is documented as the main deployment path. |
| SQLite as production database | Some older/local documentation references SQLite, but the production Compose file and requested stack use PostgreSQL. |

## H.12 Academic Summary

The FRAS production deployment uses a containerized architecture in which Docker Compose coordinates the PostgreSQL database, FastAPI backend, and Nginx-served Angular/Ionic frontend. The backend is built from a Python 3.11 image and runs Uvicorn on port `8000`, while the frontend service exposes the user interface on port `8080` and proxies API requests to the backend. PostgreSQL persists application data through a named Docker volume, while face image data is mounted into the backend container through the dataset directory. This deployment design separates presentation, application logic, and data storage into independent services, making the system easier to configure, restart, verify, and migrate for production or capstone demonstration use.
