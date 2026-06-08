# FRAS V2 Local Setup

This guide is for setting up a local FRAS V2 development database without accidentally deleting existing data.

## 1. Install PostgreSQL

Install these PostgreSQL components locally:

- PostgreSQL Server
- Command Line Tools
- pgAdmin 4, optional but useful for viewing tables

Stack Builder is optional. FRAS V2 does not need it for local development.

During installation, remember the `postgres` password you set. You will use it in `DATABASE_URL`.

## 2. Create the V2 Database

Open pgAdmin or PSQL and create an empty database:

```sql
CREATE DATABASE fras_v2;
```

If using pgAdmin, create or select a local server connection:

- Host: `localhost`
- Port: `5432`
- Database: `postgres` first, then create/select `fras_v2`
- User: `postgres`
- Password: your local PostgreSQL password

## 3. Create `.env`

Create a `.env` file in the project root:

```text
DATABASE_URL=postgresql://postgres:<YOUR_POSTGRES_PASSWORD>@localhost:5432/fras_v2
JWT_SECRET=dev-local-secret-change-before-production
DATASET_PATH=dataset
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

If the PostgreSQL password has special characters, URL-encode them.

Examples:

- `%` becomes `%25`
- `@` becomes `%40`
- `#` becomes `%23`
- space becomes `%20`

## 4. Initialize an Empty V2 Schema

Run this only for a fresh database or when you intentionally want to reset V2 tables:

```powershell
.\.venv\Scripts\python.exe database\init_v2_database.py --force
```

Important: `--force` is destructive. It drops and recreates V2 tables.

The init script refuses to run without `--force` to prevent accidental data loss.

## 5. Seed Development Data

Use the faculty load document as the seed source:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "<FULL_PATH_TO_FRAS-prof-database.docx>"
```

Example:

```powershell
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "C:\Users\YourName\Downloads\FRAS REVISIONS\FRAS-prof-database.docx"
```

This seed command is additive by default. It creates or updates:

- professor accounts
- professor profiles
- courses
- rooms
- classes and schedules
- sample students
- enrollments
- the special test professor account

It should not reset the whole database.

## 6. Test Accounts

Development-only accounts:

| Account Type | Email | Password |
| --- | --- | --- |
| Test professor | `test.professor@fras.local` | `password123` |
| Faculty-load professors | generated from professor names, usually `lastname.firstname@mapua.test` style | `password` |

The exact imported professor emails can be checked with:

```powershell
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
```

## 7. Verify Database Contents

List V2 tables:

```powershell
.\.venv\Scripts\python.exe database\check_v2_database.py
```

Verify seeded professors, login, classes, students, and enrollments:

```powershell
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
```

## 8. Safe vs Destructive Commands

Safe or additive commands:

```powershell
.\.venv\Scripts\python.exe database\check_v2_database.py
.\.venv\Scripts\python.exe database\verify_v2_integration_seed.py
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "<FULL_PATH_TO_FRAS-prof-database.docx>"
.\.venv\Scripts\python.exe database\create_v2_test_professor.py
```

Destructive or data-replacing commands:

```powershell
.\.venv\Scripts\python.exe database\init_v2_database.py --force
.\.venv\Scripts\python.exe database\seed_v2_from_v1.py --force
.\.venv\Scripts\python.exe database\seed_v2_integration_data.py --docx "<FULL_PATH_TO_FRAS-prof-database.docx>" --replace-docx-schedules
```

Use destructive commands only when you intentionally want to reset or replace data.

## 9. Run Backend

From the project root:

```powershell
.\.venv\Scripts\python.exe backend.py
```

If the backend starts successfully, it should include the V2 router in the startup logs.

## 10. Run Frontend

From the Angular project folder:

```powershell
cd facial-attendance
npm start
```

Open:

```text
http://localhost:4200
```

## 11. Suggested Future Wrapper

A safer wrapper can be added later:

```text
database/setup_v2_dev_database.py
```

Recommended behavior:

- check whether `DATABASE_URL` is set
- check whether the target database exists
- show the target database name before running anything
- ask for an explicit `--reset` flag before calling `init_v2_database.py --force`
- run additive seed by default
- print test accounts at the end

Until that wrapper exists, use the commands above carefully.
