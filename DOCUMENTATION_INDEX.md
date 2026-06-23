# FRAS V2 Documentation Index

This repository contains both legacy FRAS V1 material and the final FRAS V2 implementation. For thesis, appendix, and reviewer use, treat FRAS V2 as the current system scope.

## Start Here

| Document | Purpose |
|---|---|
| `README.md` | GitHub project overview focused on FRAS V2 |
| `docs/V2_WORKFLOW.md` | Final professor-centered classroom presence monitoring workflow |
| `docs/FRAS_V2_USER_MANUAL.md` | User manual for professors/instructors |
| `docs/QA_TEST_PLAN.md` | V2 QA strategy and validation scope |
| `docs/TEST_CASES.md` | V2 functional, UI, and negative test cases |

## V2 Technical Documentation

| Document | Purpose |
|---|---|
| `docs/V2_PRODUCT_VISION.md` | Product vision and V1-to-V2 distinction |
| `docs/V2_DATABASE_DESIGN.md` | V2 database design overview |
| `database/v2_schema.sql` | Implemented V2 PostgreSQL schema |
| `docs/V2_LOCAL_SETUP.md` | Local V2 setup notes |
| `docs/V2_DOCKER_DEPLOYMENT.md` | Docker deployment guide for V2 |
| `docs/V2_CONTAINERIZATION_RUNBOOK.md` | Practical V2 containerization and verification runbook |
| `docs/V2_VPS_REPLACE_DEPLOY.md` | VPS replacement deployment notes |
| `docs/V2_BUSINESS_RULES.md` | Attendance and session behavior rules |

## Appendix-ready Thesis Evidence

| Document | Purpose |
|---|---|
| `FRAS_V2_APPENDICES_EVIDENCE.md` | Combined appendix evidence package |
| `FRAS_V2_APPENDIX_D_API_DOCUMENTATION.md` | Appendix D API documentation for V2 |
| `FRAS_V2_APPENDIX_M_PROJECT_TIMELINE.md` | Appendix M timeline and Git activity |
| `FRAS_V2_REPRESENTATIVE_FINALIZED_SESSION_CHAPTER_4_EVIDENCE.md` | Representative finalized Session 3 evidence |
| `FRAS_V2_CHAPTER_4_TESTING_RESULTS.md` | Testing and validation evidence |
| `FRAS_V2_CHAPTER_4_DATABASE_SUMMARY.md` | Database summary evidence |
| `FRAS_V2_CHAPTER_4_IMPLEMENTATION_EVIDENCE.md` | Implementation evidence |
| `FRAS_V2_MERMAID_DIAGRAMS_FOR_THESIS.md` | Mermaid diagrams for thesis use |

## Main Source Folders

| Area | Path |
|---|---|
| V2 backend | `v2/` |
| V2 database scripts | `database/*v2*`, `database/v2_schema.sql` |
| V2 frontend | `facial-attendance/src/app/v2/` |
| Face embeddings | `services/face_embeddings.py` |
| V2 tests | `tests/test_v2_*.py` |
| V2 Docker deployment | `docker-compose.v2.yml`, `Dockerfile.backend.v2`, `facial-attendance/Dockerfile.v2` |

## Current Official Direction

| Area | Decision |
|---|---|
| Final thesis system | FRAS V2 |
| Primary workflow | Professor-centered classroom presence monitoring |
| Backend | FastAPI with V2 router under `/api/v2` |
| Frontend | Angular/Ionic V2 pages under `facial-attendance/src/app/v2/` |
| Database | PostgreSQL V2 schema |
| Recognition | Face profile images plus stored embeddings |
| Export | Blackboard-ready CSV generated in the frontend after finalization |
| Legacy V1/admin material | Historical background only, not final V2 scope |

## Legacy or Background Documentation

Some older documents describe V1, admin-heavy workflows, SQLite demo behavior, or earlier deployment plans. These files may still be useful for history, but they should not be used as the final V2 thesis scope unless clearly marked as background.
