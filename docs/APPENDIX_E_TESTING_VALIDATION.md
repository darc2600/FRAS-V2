# Appendix E: Testing and Validation

## E.1 Overview

This appendix documents the system testing and validation artifacts available in the Facial Recognition Attendance System (FRAS) repository. It summarizes smoke tests, end-to-end tests, backend validation scripts, and the evidence collected for operational verification.

The repository includes automated test scripts, generated JSON reports, and test files that exercise the following system areas:

- API availability and endpoint coverage
- authentication and role-based access control
- file upload registration and recognition flows
- support ticket workflows and schedule management
- attendance logging and database insertion
- end-to-end student registration and recognition

## E.2 Smoke Test Artifacts

The `tools/` folder contains scripts that perform automated smoke testing and save structured results.

### Core smoke-test scripts

- `tools/smoke_test_apis.py`
  - Fetches `/openapi.json`
  - Tests public GET endpoints
  - Verifies admin endpoint `403` without auth and `200` with valid auth
  - Writes `tools/smoke_test_results.json`

- `tools/smoke_test_apis_extended.py`
  - Extends GET coverage across the API
  - Writes `tools/smoke_test_extended_results.json`

- `tools/smoke_test_post.py`
  - Creates and deletes a user via `/api/admin/users`
  - Writes `tools/smoke_test_post_results.json`

- `tools/smoke_test_write_extended.py`
  - Tests support ticket creation, update, and replies
  - Tests room schedule create/delete flows
  - Writes `tools/smoke_test_write_extended_results.json`

- `tools/smoke_test_files_and_attendance.py`
  - Tests multipart registration upload via `/api/registration`
  - Tests `/api/capture`
  - Tests `/api/recognize`
  - Tests `/api/attendance`
  - Writes `tools/smoke_test_files_and_attendance_results.json`

### Smoke test report

- `tools/api_test_report.md`
  - Generated report of tested endpoints and safe write flows
  - Summarizes which GET endpoints returned `200`, which admin endpoints required auth, and which endpoints remain untested

## E.3 End-to-End and Integration Validation

The repository also includes end-to-end scripts and integration tests that validate the complete attendance workflow.

### Key E2E validation

- `tests/test_e2e_attendance.py`
  - Validates dataset availability and copies sample student face images
  - Creates a classroom schedule for the current day
  - Registers a new student with images using the `/api/registration` endpoint
  - Calls `/api/recognize` with a captured face image
  - Verifies that an attendance log is inserted in `attendance.db`
  - Cleans up created student records, enrollments, embeddings, attendance logs, and temporary data

- `integration_test.py`
  - Provides a full integration test runner for the system
  - Can be used as a higher-level validation script for backend workflows

## E.4 Backend Test Coverage

The FRAS repository includes targeted backend and functional tests for core modules.

### Backend test scripts

- `test_backend.py`
- `test_backend_logic.py`
- `test_flask_server.py`
- `test_registration.py`
- `test_user_management.py`
- `test_system_settings.py`
- `test_support_ticket.py`
- `test_super_admin_flow.py`
- `test_server.py`
- `test_query.py`
- `test_import.py`
- `test_attendance_export.py`

These scripts support validation of authentication, user management, registration logic, support ticket workflows, attendance export, and server APIs.

## E.5 Validated Functional Areas

The available test artifacts demonstrate validation for these functional areas:

- OpenAPI accessibility and API endpoint reachability
- JWT login and bearer token retrieval
- Role-based access control for protected admin routes
- Safe create/delete user operations
- Support ticket creation, update, and replies
- Room schedule creation and deletion
- Multipart file uploads for registration and recognition
- Attendance retrieval and log verification
- Database insertion and relational consistency

## E.6 Evidence and Documentation Links

The following repository files document the existing test evidence and operational validation findings:

- `docs/OPERATIONAL_VALIDATION_EVIDENCE.md`
  - Summarizes recognition, API, database, deployment, and smoke-test evidence

- `tools/api_test_report.md`
  - Summarizes API endpoint coverage and the smoke-test status of tested endpoints

- `tools/smoke_test_results.json`
- `tools/smoke_test_extended_results.json`
- `tools/smoke_test_post_results.json`
- `tools/smoke_test_write_extended_results.json`
- `tools/smoke_test_files_and_attendance_results.json`

## E.7 Known gaps and recommendations

The current test evidence also highlights some gaps that can be addressed in future validation work:

- `/api/attendance` requires valid `course_code` and `section` parameters; the core smoke test report notes this endpoint returned `422` when unparameterized
- File upload endpoints can be expanded with dedicated tests for `/api/capture`, `/api/registration`, and `/api/recognize`
- Admin bulk write endpoints and export endpoints are not fully covered by the current smoke tests
- More structured recognition metrics and logs would improve validation for confidence, similarity, response duration, and duplicate-prevention behavior

## E.8 Usage notes

To use these tests in your development or CI workflow, run the smoke-test scripts from the repository root with the backend service available at `http://127.0.0.1:8000`.

Example:

```bash
python tools/smoke_test_apis.py
python tools/smoke_test_files_and_attendance.py
```

For end-to-end validation, run the pytest test directly:

```bash
pytest tests/test_e2e_attendance.py
```
