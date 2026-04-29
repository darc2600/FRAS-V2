# FRAS Upgrade Roadmap

This roadmap tracks the planned PR-based cleanup and upgrade sequence for the latest branch.

## Fix 1 — Repo Stabilization and Documentation Cleanup

Status: In progress

Scope:

- Rewrite README as a project showcase
- Add dedicated setup/deployment/demo/troubleshooting docs
- Add `.env.example`
- Improve `.gitignore`
- Define official backend and database direction

## Fix 2 — Docker and Environment Cleanup

Scope:

- Convert Dockerfile to valid UTF-8
- Clean Docker build flow
- Move secrets to environment variables
- Update production compose guidance

## Fix 3 — Small Panel Feedback Fixes

Scope:

- Add Contact Support placeholders
- Rename Create User to Add User
- Add user-management filter icon/collapsible filter panel

## Fix 4 — Duplicate Room Protection

Scope:

- Normalize room numbers
- Prevent duplicate room creation
- Add unique database index
- Show clear frontend duplicate warning

## Fix 5 — Attendance Reports Polish

Scope:

- Clean report form controls
- Improve table display
- Add better no-data states
- Clarify export actions

## Fix 6 — Analytics Charts

Scope:

- Monthly student registration chart
- Monthly instructor registration chart
- Monthly attendance chart
- Attendance status distribution chart
- Clearer face-registration metrics

## Fix 7 — Repeatable Demo Data Workflow

Scope:

- Add reset demo data script
- Seed clean demo users, classes, rooms, attendance logs, and support tickets
- Document demo accounts and demo flow

## Fix 8 — Security Hardening

Scope:

- Remove dev fallback secrets
- Remove plaintext password fallback
- Remove password debug logs
- Add stricter environment validation
