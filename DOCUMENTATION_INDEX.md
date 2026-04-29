# FRAS Documentation Index

The main `README.md` now acts as a project showcase. Operational instructions are separated into focused documents under `docs/`.

| Document | Purpose |
|---|---|
| `README.md` | High-level project showcase for GitHub and reviewers |
| `docs/SETUP.md` | Local setup and run instructions |
| `docs/DEPLOYMENT.md` | Deployment strategy and environment notes |
| `docs/DEMO_GUIDE.md` | Suggested thesis/demo presentation flow |
| `docs/TROUBLESHOOTING.md` | Common issue fixes |
| `docs/ROADMAP.md` | PR-by-PR improvement plan |

## Current Official Direction

| Area | Decision |
|---|---|
| Backend | FastAPI through `backend.py` |
| Frontend | Angular/Ionic app in `facial-attendance/` |
| Demo database | SQLite through `attendance.db` |
| Future production DB | PostgreSQL optional after migration cleanup |
| Face dataset | Local `dataset/` folder |
