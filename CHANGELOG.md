# Changelog

All notable changes to FRAS are documented here.

## 2026-04-29 — Final Stabilization and Panel Feedback Update Cycle

### Added

- Showcase-style `README.md` focused on project value and system features.
- Dedicated documentation files for setup, deployment, demo flow, troubleshooting, Docker, reports, analytics, and roadmap.
- `.env.example` for safer environment configuration.
- `.dockerignore` for cleaner Docker builds.
- Nginx config for frontend-to-backend API proxying.
- Secret generator script.
- Deployment config checker script.
- Contact Support placeholder options for category and priority.
- Collapsible User Management filter panel.
- Duplicate room normalization helper.
- Duplicate room cleanup script.
- Attendance Reports polish documentation.
- Analytics chart data and clearer face registration wording.
- Repeatable demo data reset workflow.
- `CONTRIBUTORS.md` with contributor and change summary.
- Pull request templates.
- Lightweight project health checker.
- Security notes for repository hygiene.

### Changed

- README direction changed from install-only documentation into a project showcase.
- Installation and deployment instructions moved into dedicated docs.
- User-facing label `Create User` changed to `Add User`.
- Technical face-recognition labels changed to more understandable demo-friendly terms.
- SQLite is documented as the official demo database path.
- PostgreSQL is positioned as an optional future/production path.
- Attendance Reports UX improved with better filters, messages, and display behavior.
- Analytics page upgraded from static summary cards to visual insights.

### Fixed

- Broken Dockerfile encoding issue by replacing with UTF-8 content.
- Deployment proxy gap between frontend `/api` calls and FastAPI backend.
- Contact Support missing placeholder issue.
- Duplicate room creation risk in Add/Edit Schedule flow.
- Attendance Reports filter and empty-state problems.
- Confusing face embedding analytics wording.
- Demo data fragility by adding reset and seed workflow.

### Security Notes

- Real server passwords, database passwords, and JWT secrets must never be committed.
- Any credentials previously shared in documents should be rotated immediately.
- `.env` should remain local only.
- Use `.env.example` as the committed template.

### Remaining Work

- Complete auth/password reset hardening.
- Archive old debug scripts and backup files.
- Run full frontend and backend smoke tests.
- Perform final deployment test on target hosting.
- Validate demo walkthrough after running the reset demo data script.
