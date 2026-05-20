# FRAS Documentation Index

The main `README.md` now acts as a project showcase. Operational instructions are separated into focused documents under `docs/`.

| Document | Purpose |
|---|---|
| `README.md` | High-level project showcase for GitHub and reviewers |
| `docs/SETUP.md` | Local setup and run instructions |
| `docs/DEPLOYMENT.md` | Deployment strategy and environment notes |
| `docs/CHAPTER4_SYSTEM_DEPLOYMENT_DIAGRAMS.md` | Chapter 4 API communication, VPS deployment topology, and recognition workflow diagrams |
| `docs/OPERATIONAL_VALIDATION_EVIDENCE.md` | Recognition, API, database, deployment, and workflow validation evidence currently available |
| `docs/APPENDIX_C_DATABASE_SCHEMA_DOCUMENTATION.md` | Thesis Appendix C PostgreSQL database schema, relationships, attendance tables, and embedding storage documentation |
| `docs/APPENDIX_D_API_DOCUMENTATION.md` | Thesis Appendix D API documentation, endpoint summary, authentication notes, and recognition API explanation |
| `docs/APPENDIX_H_DEPLOYMENT_AND_ENVIRONMENT_CONFIGURATION.md` | Thesis Appendix H deployment workflow, environment configuration, production architecture, and Docker commands |
| `docs/DEMO_GUIDE.md` | Suggested thesis/demo presentation flow |
| `docs/TROUBLESHOOTING.md` | Common issue fixes |
| `docs/ROADMAP.md` | PR-by-PR improvement plan |

## Current Official Direction

| Area | Decision |
|---|---|
| Backend | FastAPI through `backend.py` |
| Frontend | Angular/Ionic app in `facial-attendance/` |
| Local/demo database | SQLite through `attendance.db` |
| VPS production database | PostgreSQL through Docker Compose |
| Face dataset | Local `dataset/` folder |
