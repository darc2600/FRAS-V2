<div align="center">

# FRAS — Facial Recognition Attendance System

### A full-stack attendance management platform with face recognition, schedule-aware monitoring, reports, analytics, support workflows, and admin controls.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![Angular](https://img.shields.io/badge/Angular-Frontend-DD0031?style=for-the-badge&logo=angular)
![Ionic](https://img.shields.io/badge/Ionic-Mobile%20Ready-3880FF?style=for-the-badge&logo=ionic)
![SQLite](https://img.shields.io/badge/SQLite-Demo%20Database-003B57?style=for-the-badge&logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-Deployment-2496ED?style=for-the-badge&logo=docker)

</div>

---

## Project Overview

**FRAS** is a Facial Recognition Attendance System built for academic attendance monitoring and administrative reporting. The system combines student identity records, facial data capture, class schedules, attendance logs, reports, analytics, and support workflows into one centralized platform.

This repository has been updated to become more presentation-ready, panel-ready, and maintainable. The latest update cycle focuses on stronger documentation, cleaner deployment direction, repeatable demo data, analytics improvements, report polish, and feedback-driven UI updates.

---

## What FRAS Does

FRAS helps schools or departments manage attendance with a more automated and auditable flow:

1. Administrators manage users, students, instructors, rooms, classes, and schedules.
2. Students register profile and face data.
3. The system supports face-recognition attendance workflows.
4. Attendance records are stored and made available for review.
5. Admin users can generate reports and review analytics.
6. Support tickets and system settings help manage operations.

---

## Core Modules

| Module | Description |
|---|---|
| Authentication | Login and protected admin access flow. |
| User Management | Admin, instructor, and student account management. |
| Student Management | Student records, identifiers, and face registration readiness. |
| Instructor Management | Instructor records used for class and report workflows. |
| Face Registration | Captures and stores student facial reference data. |
| Face Recognition | Supports automated attendance workflows using registered faces. |
| Schedule Management | Manages rooms, classes, instructors, and schedule assignments. |
| Attendance Logs | Stores attendance records for reporting and analysis. |
| Attendance Reports | Provides class and professor attendance report views. |
| System Analytics | Shows student, instructor, attendance, and face registration insights. |
| Contact Support | Allows users to submit support requests with category and priority. |
| System Settings | Central place for configurable system behavior. |

---

## Latest Update Highlights

### Documentation and Repository Polish

- Showcase-style README.
- Dedicated setup, deployment, demo, troubleshooting, and roadmap docs.
- Contributor and changelog tracking.
- Pull request templates for cleaner GitHub workflow.

### Deployment and Environment Cleanup

- Fixed Dockerfile direction.
- Added Nginx frontend-to-backend proxy notes.
- Added safe `.env.example` pattern.
- Added deployment validation script.
- Added secret generator utility.

### Panel Feedback Fixes

- Contact Support now uses placeholder selections.
- `Create User` wording was changed to `Add User`.
- User Management filters were cleaned up.
- Reports display was polished.
- Analytics now includes visual insight direction.
- Face embedding wording was replaced with clearer face registration wording.

### Reliability Improvements

- Duplicate room protection.
- Room number normalization.
- Duplicate room cleanup script.
- Repeatable demo data reset workflow.
- Demo database backup before reset.

---

## System Architecture

```txt
FRAS
├── Angular/Ionic Frontend
│   ├── Login
│   ├── Admin Dashboard
│   ├── User Management
│   ├── Attendance Reports
│   ├── Analytics
│   ├── Schedule Management
│   └── Support UI
│
├── FastAPI Backend
│   ├── Auth APIs
│   ├── Admin APIs
│   ├── Attendance APIs
│   ├── Recognition APIs
│   ├── Schedule APIs
│   └── Support APIs
│
├── Database Layer
│   ├── SQLite demo database
│   ├── Repository modules
│   ├── Migration helpers
│   └── Demo data reset script
│
└── Deployment Layer
    ├── Dockerfile
    ├── Docker Compose
    ├── Nginx proxy config
    └── Environment templates
```

---

## Recommended Demo Direction

For thesis and panel review, the recommended official demo path is:

| Area | Recommended Choice |
|---|---|
| Backend | FastAPI |
| Frontend | Angular/Ionic |
| Demo Database | SQLite |
| Demo Data | `scripts/reset_demo_data.py` |
| Deployment | Docker/Nginx after local validation |
| PostgreSQL | Future/optional production path |

This keeps the demo stable and avoids unnecessary database/deployment confusion.

---

## Demo Readiness Features

FRAS now includes a repeatable demo workflow:

- Backup existing database.
- Reset database to clean demo state.
- Seed users, students, instructors, classes, rooms, schedules, attendance logs, support tickets, and face registration coverage.
- Provide consistent demo accounts.
- Support analytics charts across monthly attendance and registration data.

See:

```txt
docs/DEMO_GUIDE.md
docs/DEMO_DATA_RESET.md
```

---

## Documentation

| File | Purpose |
|---|---|
| `DOCUMENTATION_INDEX.md` | Quick map of all major docs. |
| `docs/SETUP.md` | Local development setup. |
| `docs/DEPLOYMENT.md` | Deployment direction and server notes. |
| `docs/DOCKER_NOTES.md` | Docker-specific notes. |
| `docs/DEMO_GUIDE.md` | Suggested demo walkthrough. |
| `docs/DEMO_DATA_RESET.md` | Demo data reset workflow. |
| `docs/TROUBLESHOOTING.md` | Common issues and fixes. |
| `docs/ROADMAP.md` | Planned development sequence. |
| `docs/PROJECT_STATUS_REPORT.md` | Current system status. |
| `docs/SECURITY_NOTES.md` | Security and credential-handling notes. |
| `CONTRIBUTORS.md` | Contributors and update-cycle change summary. |
| `CHANGELOG.md` | Project change history. |

---

## Repository Health Check

A lightweight project checker is included:

```bash
python scripts/project_health_check.py
```

It checks for common issues such as:

- Missing important files.
- Dockerfile encoding problems.
- Local `.env` visibility.
- Sensitive placeholder patterns.

---

## Business and Thesis Value

FRAS is designed to demonstrate more than simple attendance tracking. It shows a complete system workflow:

- Identity and access management.
- Face registration and recognition readiness.
- Schedule-aware attendance tracking.
- Operational dashboards.
- Reports and analytics.
- Support request handling.
- Deployment and demo preparation.
- Maintainable full-stack project structure.

This makes it suitable as a thesis system, portfolio project, and base for a real attendance-monitoring product.

---

## Current Roadmap

Completed in latest update cycle:

- Documentation polish.
- Docker/environment cleanup.
- Panel feedback UI fixes.
- Duplicate room protection.
- Attendance Reports polish.
- Analytics charts and clearer face registration wording.
- Repeatable demo data reset workflow.
- Contributor and PR workflow documentation.

Recommended next:

1. Security hardening for auth and password reset.
2. Archive old debug scripts and backup files.
3. Add automated smoke tests.
4. Run final deployment validation.
5. Final UI polish for dashboard/login if time allows.

---

## Security Reminder

Do not commit real credentials.

Never commit:

- `.env`
- Server passwords
- Database passwords
- JWT secrets
- SSH credentials
- Production database dumps
- Sensitive feedback documents

Use:

```txt
.env.example
```

as the safe template.

---

## Project Status

FRAS is now significantly closer to being demo-ready and panel-ready. The project already had strong core functionality; the latest updates improve structure, clarity, visual reporting, deployment direction, and repeatable demo preparation.

