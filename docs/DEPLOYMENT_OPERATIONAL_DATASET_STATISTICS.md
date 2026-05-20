# Deployment Operational Dataset Statistics

This document summarizes the current operational dataset statistics inspected from the live FRAS deployment. The values in this document are based only on factual data found in the deployed PostgreSQL database, deployed dataset folder, Docker containers, and existing validation artifacts.

Inspection date: May 18, 2026  
Deployment host: `92.205.61.8`  
Application path: `/home/frasijbmapua/FRAS`  
Dataset path: `/home/frasijbmapua/FRAS/dataset`  
Database: PostgreSQL database `frasdb`  
Deployment services: `fras-backend-1`, `fras-frontend-1`, `fras-db-1`

## 1. Deployment Environment Summary

The live FRAS deployment is running through Docker containers. The backend is served by the `fras-backend-1` container, the frontend is served through the `fras-frontend-1` Nginx container, and the production database is served by the `fras-db-1` PostgreSQL container.

| Component | Deployment Detail |
|---|---|
| Backend container | `fras-backend-1` |
| Frontend container | `fras-frontend-1` |
| Database container | `fras-db-1` |
| Database engine | PostgreSQL |
| Database name | `frasdb` |
| Dataset folder | `/home/frasijbmapua/FRAS/dataset` |
| Application folder | `/home/frasijbmapua/FRAS` |

## 2. Student And Face Dataset Statistics

| Metric | Current Deployment Value |
|---|---:|
| Total registered students | 150 |
| Students with registered facial image paths | 57 |
| Students with stored face embeddings | 56 |
| Total stored face embeddings | 56 |
| Dataset student folders with images | 56 |
| Total face image samples stored | 280 |
| Average number of face samples per student with images | 5.0 |
| Face sample distribution | 56 students have 5 images each |

The production dataset contains 280 stored face image samples across 56 student folders. Each student folder with images contains five face samples.

## 3. Image Resolution Details

| Image Resolution | Number Of Images |
|---|---:|
| `1280x720` | 235 |
| `640x480` | 45 |
| Total | 280 |

The deployed face dataset contains two observed image resolutions: `1280x720` and `640x480`.

## 4. Attendance Dataset Statistics

| Metric | Current Deployment Value |
|---|---:|
| Total attendance logs | 265 |
| Total recognized attendance entries | 248 |
| Total attendance sessions recorded | 20 distinct class-date sessions |

Recognized attendance entries were identified from attendance log notes containing the phrase `Face recognized`.

### Attendance Status Breakdown

| Attendance Status | Count |
|---|---:|
| Present | 27 |
| Late | 28 |
| Absent | 210 |
| Total | 265 |

## 5. Account, Course, Class, And Section Statistics

| Metric | Current Deployment Value |
|---|---:|
| Total user accounts | 15 |
| Active user accounts | 14 |
| Instructor user accounts | 10 |
| IT admin accounts | 3 |
| Super admin accounts | 2 |
| Total instructors | 10 |
| Total courses | 93 |
| Total classes | 20 |
| Distinct sections | 14 |

### User Role Breakdown

| User Role | Total Accounts | Active Accounts |
|---|---:|---:|
| Instructor | 10 | 9 |
| IT Admin | 3 | 3 |
| Super Admin | 2 | 2 |
| Total | 15 | 14 |

## 6. Support Ticket Statistics

| Metric | Current Deployment Value |
|---|---:|
| Total support tickets | 22 |

### Ticket Status Breakdown

| Ticket Status | Count |
|---|---:|
| Open | 16 |
| In Progress | 1 |
| Resolved | 3 |
| Closed | 2 |
| Total | 22 |

### Ticket Priority Breakdown

| Ticket Priority | Count |
|---|---:|
| Critical | 5 |
| High | 6 |
| Medium | 6 |
| Low | 5 |
| Total | 22 |

## 7. Recognition Metrics And Operational Logs

The deployment was inspected for stored recognition metrics, timing values, confidence values, recognition attempts, and failed recognition records.

| Item Checked | Finding |
|---|---|
| Timing metrics | No structured database columns were found for recognition processing time, request duration, or elapsed recognition time. |
| Recognition confidence values | No structured database columns were found for confidence, similarity score, distance score, or recognition confidence. |
| Recognition attempts | No dedicated database table was found for all recognition attempts. |
| Failed recognitions | No dedicated database table was found for failed recognition attempts. |
| Operational backend logs | Docker backend logs exist and include runtime debug messages such as similarity and threshold values. |
| Persisted recognition scores | Recognition similarity values appear in runtime logs but are not persisted as structured database records. |

The deployed database contains `attendance_logs` and `audit_logs`, but no separate recognition-attempt table was found. Therefore, failed recognition attempts and recognition confidence values cannot be counted from the production database.

## 8. API Test Reports And Deployment Validation Artifacts

The deployed application folder contains existing API and smoke-test artifacts.

| Artifact | Status |
|---|---|
| `tools/api_test_report.md` | Present |
| `tools/smoke_test_results.json` | Present |
| `tools/smoke_test_extended_results.json` | Present |
| `tools/smoke_test_post_results.json` | Present |
| `tools/smoke_test_write_extended_results.json` | Present |
| `tools/smoke_test_files_and_attendance_results.json` | Present |
| `tools/full_flow_attendance_test_results.json` | Present |
| `scripts/project_health_check.py` | Present |

The API test report indicates that OpenAPI was reachable, super administrator login succeeded, several public and admin GET endpoints were tested, and selected write flows such as user creation/deletion, support ticket handling, and room schedule creation/deletion were tested.

The same report identifies some endpoints as untested or partially tested, including file-upload endpoints and the recognition endpoint in that specific API smoke-test report.

## 9. Thesis-Ready Summary

The live FRAS deployment contains 150 registered students, with 57 students having registered facial image paths and 56 students having stored face embeddings. The deployed facial dataset contains 280 image samples across 56 student folders, with five samples stored for each face-registered student. The observed image resolutions are `1280x720` for 235 images and `640x480` for 45 images. The attendance database contains 265 attendance logs, including 248 records identified as face-recognized attendance entries through attendance log notes. The attendance records include 27 Present entries, 28 Late entries, and 210 Absent entries across 20 distinct class-date attendance sessions.

The operational database also contains 15 user accounts, including 10 instructor accounts, 3 IT admin accounts, and 2 super admin accounts. The academic data includes 93 courses, 20 classes, and 14 distinct sections. The support ticket module contains 22 tickets, distributed across open, in-progress, resolved, and closed statuses.

No structured database records were found for recognition confidence values, processing time, recognition attempts, or failed recognition attempts. Runtime backend logs contain some debug information related to recognition similarity and threshold values, but these values are not stored in a dedicated database table. API test reports and smoke-test result files are present in the deployed application folder and provide evidence of endpoint validation and selected workflow testing.

