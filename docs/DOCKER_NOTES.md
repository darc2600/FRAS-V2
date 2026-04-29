# Docker Notes

## Fix included in this patch

The previous Dockerfile was saved as UTF-16 text. Docker expects a normal text Dockerfile, so this patch replaces it with a clean UTF-8 Dockerfile.

## Frontend and backend routing

The Angular app uses relative API URLs. That means browser requests go to the same domain as the frontend, for example:

```txt
/api/login
/api/admin/users
```

Because of that, the Nginx frontend container must proxy `/api/*` to the FastAPI backend container. This patch adds:

```txt
nginx/default.conf
```

## Official demo database mode

This patch keeps the project in SQLite demo mode:

```txt
attendance.db -> /app/attendance.db
```

PostgreSQL is intentionally not started by default because the current project data and panel demo flow are easier to stabilize with SQLite first.
