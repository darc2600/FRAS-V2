# FRAS Local Setup Guide

This file contains the actual setup instructions for running FRAS locally. The main README is intentionally written as a project showcase.

## Official Local Demo Stack

For the current branch, use this setup:

| Layer | Official Local Choice |
|---|---|
| Backend | FastAPI through `backend.py` |
| Frontend | Angular/Ionic app in `facial-attendance/` |
| Database | SQLite using `attendance.db` |
| Face images | Local `dataset/` folder |

PostgreSQL support exists, but SQLite is the recommended demo path until deployment is finalized.

---

## Backend Setup

From the project root:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
.venv\Scripts\activate
```

Install backend packages:

```bash
pip install fastapi uvicorn python-multipart pyjwt passlib bcrypt pydantic
```

Run the backend:

```bash
uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```txt
http://127.0.0.1:8000
```

---

## Frontend Setup

From the project root:

```bash
cd facial-attendance
npm install
npm start
```

Frontend URL:

```txt
http://localhost:4200
```

The frontend uses relative API paths in the latest branch, so it is deployment-friendly when served behind the same domain/proxy.

---

## Recommended Local Run Order

Terminal 1:

```bash
uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd facial-attendance
npm start
```

---

## Important Local Files

| File/Folder | Purpose |
|---|---|
| `backend.py` | Main FastAPI backend |
| `attendance.db` | Current SQLite demo database |
| `dataset/` | Student face image dataset |
| `facial-attendance/` | Angular/Ionic frontend |
| `.env.example` | Environment variable template |

---

## Notes

- Do not commit real `.env` files.
- Do not commit real server passwords.
- Treat `attendance.db` as the current demo database unless the deployment branch is changed to PostgreSQL.
- If the frontend cannot find `ng`, run `npm install` inside `facial-attendance/` first.
