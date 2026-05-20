# Appendix D: API Documentation

## D.1 Overview

This appendix documents the application programming interface (API) of the Facial Recognition Attendance System (FRAS). The backend is implemented using FastAPI and is served through `backend.py`, which initializes the FastAPI application, configures Cross-Origin Resource Sharing (CORS), defines several direct API routes, and includes modular routers from the `api/` directory.

The API follows a resource-oriented structure and exposes endpoints for authentication, room and schedule retrieval, student registration, image capture, facial recognition, attendance retrieval, administrative user management, system settings, support tickets, analytics, and report export. Most data is exchanged in JSON format. Endpoints that accept images use `multipart/form-data`.

Unless otherwise stated, the base URL used in the examples is:

```text
http://127.0.0.1:8000
```

## D.2 Authentication Model

The system provides JSON Web Token (JWT) authentication through the login endpoint. A successful login returns a bearer token, user type, permissions, and user identifier. Administrative endpoints use FastAPI dependencies that validate the bearer token and enforce role-based permissions.

The following roles and permission groups are represented in the backend:

- `regular`: ordinary user or student-level account.
- `instructor`: instructor account with attendance, schedule, registration, and support permissions.
- `it_admin`: administrative account with user-management and support-management permissions.
- `super_admin`: highest-level administrative account with full system and configuration permissions.

The token must be sent in protected requests using the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Authentication applicability observed in the backend:

| Endpoint group | Backend authentication requirement |
|---|---|
| Login | Not required |
| Admin user management | Required |
| Admin system settings | Required |
| Admin analytics | Required |
| Admin attendance export | Required |
| Admin support ticket management | Required |
| User support ticket creation | Required in the active `backend.py` endpoint |
| Face recognition, registration, capture, attendance retrieval, room/schedule lookup | No backend token dependency is enforced in the inspected implementation |
| Public debug face-embedding coverage | Not required; identified in code as temporary/local verification endpoint |

Not applicable or not fully enforceable from the inspected backend: backend-level authentication is not applied to the attendance recognition endpoint, student registration endpoint, image capture endpoint, attendance retrieval endpoint, and general lookup endpoints. If these operations are restricted in practice, the restriction is likely handled by the frontend route guard or deployment configuration rather than by the FastAPI route dependency itself.

## D.3 Endpoint Summary

| Module | Method | Endpoint | Description | Authentication |
|---|---:|---|---|---|
| Authentication | POST | `/api/login` | Authenticates a user and returns a JWT. | No |
| Authentication | POST | `/login` | Backward-compatible alias for login. | No |
| Rooms | GET | `/api/rooms` | Returns available rooms. | No backend enforcement |
| Rooms | GET | `/api/rooms/{room_id}/courses` | Returns courses assigned to a room. | No backend enforcement |
| Rooms | GET | `/api/rooms/{room_id}/courses/{course_code}/sections` | Returns sections for a course in a room. | No backend enforcement |
| Rooms | GET | `/api/floors` | Returns available floor levels. | No backend enforcement |
| Rooms | GET | `/api/floors/{floor_level}/rooms` | Returns rooms located on a floor. | No backend enforcement |
| Rooms | GET | `/api/rooms/{room_id}/courses-sections` | Returns course-section combinations for a room. | No backend enforcement |
| Courses | GET | `/api/courses` | Returns course codes and names. | No backend enforcement |
| Courses | GET | `/api/courses/{course_code}/sections` | Returns sections for a course. | No backend enforcement |
| Instructors | GET | `/api/instructors` | Returns instructor names. | No backend enforcement |
| Students | GET | `/api/students` | Returns student list for selection. | No backend enforcement |
| Students | GET | `/api/students/{student_number}` | Returns student details by student number. | No backend enforcement |
| Classes | GET | `/api/classes` | Returns class identifiers and metadata. | No backend enforcement |
| Attendance | GET | `/api/attendance` | Retrieves attendance records by course and section. | No backend enforcement |
| Registration | POST | `/api/registration` | Registers or updates a student with schedule and face images. | No backend enforcement |
| Registration | POST | `/api/register` | Direct backend alias for student registration. | No backend enforcement |
| Capture | POST | `/api/capture` | Stores a captured student face image. | No backend enforcement |
| Recognition | POST | `/api/recognize` | Performs face recognition and records attendance. | No backend enforcement |
| Recognition | POST | `/api/mark-absents` | Marks absent students for a class and date. | No backend enforcement |
| Schedule | GET | `/api/room-schedule/{room_code}` | Retrieves room schedule data. | No backend enforcement |
| Schedule | POST | `/api/room-schedule/{room_code}` | Updates room schedule data. | No backend enforcement |
| Schedule | DELETE | `/api/room-schedule/{room_code}` | Deletes room schedule data. | No backend enforcement |
| Administration | GET | `/api/admin/users` | Lists managed users. | Required: `manage_users` |
| Administration | POST | `/api/admin/users` | Creates an instructor, IT admin, or super admin account. | Required: `manage_users` |
| Administration | PUT | `/api/admin/users/{user_id}` | Updates user email, role, or active status. | Required: `manage_users` |
| Administration | DELETE | `/api/admin/users/{user_id}` | Deletes a user. | Required: `manage_users` |
| Administration | POST | `/api/admin/reset-password` | Resets a user password. | Required: `reset_passwords` |
| Administration | POST | `/api/admin/users/bulk` | Activates, deactivates, or deletes multiple users. | Required: `manage_users` |
| Administration | GET | `/api/admin/system-settings` | Retrieves configurable system settings. | Required: `system_config` |
| Administration | PUT | `/api/admin/system-settings` | Updates one system setting. | Required: `system_config` |
| Administration | PUT | `/api/admin/system-settings/bulk` | Updates multiple system settings. | Required: `system_config` |
| Administration | GET | `/api/admin/analytics` | Returns attendance and user analytics. | Required: `view_all_data` |
| Administration | POST | `/api/admin/mark-automatic-absents` | Triggers automatic absent marking. | Required: `manage_users` |
| Administration | GET | `/api/admin/face-embedding-coverage` | Returns face-embedding coverage statistics. | Required: `view_all_data` |
| Support | POST | `/api/support/tickets` | Creates a support ticket for an authenticated user. | Required |
| Support | GET | `/api/admin/support/tickets` | Lists support tickets. | Required: `manage_support` |
| Support | PUT | `/api/admin/support/tickets/{ticket_id}` | Updates support ticket status, priority, or assignee. | Required: `manage_support` |
| Support | POST | `/api/admin/support/tickets/{ticket_id}/replies` | Adds a reply to a support ticket. | Required: `manage_support` |
| Support | GET | `/api/admin/support/tickets/{ticket_id}/replies` | Lists replies for a support ticket. | Required: `manage_support` |
| Reports | POST | `/api/admin/attendance/export` | Exports attendance report in JSON, CSV, Excel, or PDF. | Required: `view_all_data` |
| Reports | POST | `/api/admin/attendance/export/professor` | Exports professor-level attendance report. | Required: `view_all_data` |
| Debug | GET | `/api/debug/face-embedding-coverage-public` | Public face-embedding coverage check. | No |
| Debug | GET | `/test` | Basic health check returning `OK`. | No |

## D.4 Sample API Requests and Responses

### D.4.1 User Login

Description: Authenticates a user and returns a bearer token for protected administrative endpoints.

HTTP method and endpoint:

```http
POST /api/login
Content-Type: application/json
```

Sample request:

```json
{
  "email": "admin@example.com",
  "password": "samplePassword123"
}
```

Sample successful response:

```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer",
  "user_type": "super_admin",
  "permissions": [
    "manage_users",
    "reset_passwords",
    "system_config",
    "view_all_data",
    "view_analytics"
  ],
  "user_id": 1
}
```

Sample error response:

```json
{
  "detail": "Invalid credentials"
}
```

### D.4.2 Retrieve Rooms

Description: Returns room records used by the frontend for room, course, and section selection.

HTTP method and endpoint:

```http
GET /api/rooms
```

Sample response:

```json
[
  {
    "room_id": 1,
    "room_number": "R101",
    "floor_level": 1,
    "building_name": "Main Building"
  }
]
```

### D.4.3 Retrieve Attendance

Description: Retrieves attendance entries for a selected course and section, with optional room and date filters.

HTTP method and endpoint:

```http
GET /api/attendance?course_code=CS101&section=A&room=1&start_date=2026-05-01&end_date=2026-05-19
```

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `course_code` | Yes | Course code to search. |
| `section` | Yes | Class section. |
| `room` | No | Room identifier used to narrow class selection. |
| `start_date` | No | Start date in `YYYY-MM-DD` format. |
| `end_date` | No | End date in `YYYY-MM-DD` format. |

Sample response:

```json
{
  "attendance": [
    [
      "2025103001",
      "Dela Cruz, Juan",
      "2026-05-19T09:05:10+08:00",
      "Present"
    ],
    [
      "2025103002",
      "Santos, Maria",
      "2026-05-19T09:17:22+08:00",
      "Late"
    ]
  ]
}
```

### D.4.4 Student Registration With Face Images

Description: Registers a student, stores face images, saves the face-data path, creates or updates enrollments, and attempts to generate a stored face embedding from the first uploaded image.

HTTP method and endpoint:

```http
POST /api/registration
Content-Type: multipart/form-data
```

Sample multipart fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `student_number` | Text | Yes | Student number or institutional identifier. |
| `last_name` | Text | Yes | Student last name. |
| `first_name` | Text | Yes | Student first name. |
| `email` | Text | Yes | Student email address. |
| `created_at` | Text | Yes | Registration timestamp or date string. |
| `schedule` | Text | Yes | JSON list of enrolled course-section objects. |
| `images` | File list | Yes | One or more face images. |

Sample `schedule` field:

```json
[
  {
    "course_code": "CS101",
    "section": "A",
    "room": "1"
  }
]
```

Sample successful response:

```json
{
  "status": "success",
  "message": "Student registered and images saved.",
  "image_paths": [
    "/app/dataset/2025103001/capture_1.jpg",
    "/app/dataset/2025103001/capture_2.jpg"
  ]
}
```

### D.4.5 Image Capture

Description: Stores a captured face image for a student. The backend attempts image compression using configurable quality and maximum image size settings before saving the file.

HTTP method and endpoint:

```http
POST /api/capture
Content-Type: multipart/form-data
```

Sample multipart fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | Captured face image. |
| `course_code` | Text | Yes | Course context of the capture. |
| `section` | Text | Yes | Section context of the capture. |
| `student_id` | Text | Yes | Student identifier used as dataset folder name. |

Sample successful response:

```json
{
  "status": "success",
  "message": "Compressed image saved to dataset/2025103001/capture_1.jpg"
}
```

### D.4.6 Attendance Recognition API

Description: Accepts a captured image and class identifier, performs facial recognition against enrolled students, validates the class schedule, determines attendance status, and records an attendance log when appropriate.

HTTP method and endpoint:

```http
POST /api/recognize
Content-Type: multipart/form-data
```

Sample multipart fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | Captured image to be matched. |
| `class_id` | Integer | Yes | Class against which enrolled students are evaluated. |

Sample successful response:

```json
{
  "status": "success",
  "student_id": "1",
  "student_name": "Dela Cruz",
  "attendance_status": "Present",
  "attendance_recorded": true,
  "message": null
}
```

Sample duplicate-attendance response:

```json
{
  "status": "success",
  "student_id": "1",
  "student_name": "Dela Cruz",
  "attendance_status": "Present",
  "attendance_recorded": false,
  "message": "Attendance already recorded within the last 2 minutes."
}
```

Sample no-match response:

```json
{
  "status": "failed",
  "message": "No match found"
}
```

Sample schedule-validation response:

```json
{
  "status": "failed",
  "message": "Attendance recognition time not valid: no active class schedule right now (9:00 AM - 10:30 AM)"
}
```

Recognition processing explanation:

1. The uploaded image is temporarily saved on the backend server.
2. The configured face-recognition model and recognition threshold are loaded from system settings.
3. The backend first attempts embedding-based recognition by extracting an embedding from the uploaded image and comparing it with stored embeddings for students enrolled in the selected class.
4. If no embedding match satisfies the threshold, the backend falls back to image-to-image verification using DeepFace against stored dataset images of enrolled students.
5. When a student is matched, the system validates that the selected class exists, that the current Manila day matches the scheduled class day, and that the current Manila time falls within the class start and end time.
6. The attendance status is assigned based on configurable timing thresholds:
   - within the late threshold: `Present`;
   - after the late threshold but within the absent threshold: `Late`;
   - after the absent threshold: `Absent`.
7. Before inserting a new attendance row, the backend checks whether the same student already has a record for the same class and date. If the previous record is within the configured attendance buffer, the system returns a success response but does not insert a duplicate record.
8. If the attendance entry is valid and not a duplicate, a row is inserted in `attendance_logs` with the student, class, timestamp, status, and a note indicating that the face was recognized.
9. The temporary uploaded file is deleted after processing.

### D.4.7 Mark Absents

Description: Inserts absent records for enrolled students who do not have an attendance record for the specified class and date.

HTTP method and endpoint:

```http
POST /api/mark-absents
Content-Type: multipart/form-data
```

Sample multipart fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `class_id` | Integer | Yes | Class to process. |
| `date` | Text | Yes | Attendance date in `YYYY-MM-DD` format. |

Sample response:

```json
{
  "message": "Marked 3 students as absent for class 1 on 2026-05-19"
}
```

### D.4.8 Room Schedule

Description: Retrieves, updates, or deletes schedule data for a selected room.

HTTP methods and endpoints:

```http
GET /api/room-schedule/R101
POST /api/room-schedule/R101
DELETE /api/room-schedule/R101
```

Sample GET response:

```json
{
  "schedule": [
    {
      "course_code": "CS101",
      "section": "A",
      "day_of_week": "Tuesday",
      "start_time": "09:00",
      "end_time": "10:30",
      "instructor": "Reyes, Ana"
    }
  ]
}
```

Sample POST request:

```json
[
  {
    "course_code": "CS101",
    "section": "A",
    "day_of_week": "Tuesday",
    "start_time": "09:00",
    "end_time": "10:30",
    "instructor": "Reyes, Ana"
  }
]
```

Sample DELETE response:

```json
{
  "message": "Schedule deleted successfully"
}
```

### D.4.9 Administrative User Management

Description: Allows authorized administrators to list, create, update, deactivate, delete, and reset passwords for user accounts.

HTTP methods and endpoints:

```http
GET /api/admin/users
POST /api/admin/users
PUT /api/admin/users/{user_id}
DELETE /api/admin/users/{user_id}
POST /api/admin/reset-password
POST /api/admin/users/bulk
```

Authentication:

```http
Authorization: Bearer <access_token>
```

Sample create-user request:

```json
{
  "email": "instructor@example.com",
  "password": "temporaryPassword123",
  "user_type": "instructor",
  "first_name": "Ana",
  "last_name": "Reyes"
}
```

Sample create-user response:

```json
{
  "message": "User created successfully",
  "user_id": 12,
  "role": "instructor"
}
```

Sample reset-password request:

```json
{
  "email": "instructor@example.com",
  "new_password": "newPassword123"
}
```

Sample reset-password response:

```json
{
  "message": "Password reset successfully for instructor@example.com"
}
```

### D.4.10 System Settings

Description: Allows authorized administrators to retrieve and update configurable backend settings, including recognition threshold, face recognition model, image compression options, late threshold, absent threshold, and attendance buffer.

HTTP methods and endpoints:

```http
GET /api/admin/system-settings
PUT /api/admin/system-settings?setting_key=recognition_threshold&setting_value=0.65
PUT /api/admin/system-settings/bulk
```

Authentication:

```http
Authorization: Bearer <access_token>
```

Sample bulk update request:

```json
[
  {
    "key": "recognition_threshold",
    "value": "0.65"
  },
  {
    "key": "attendance_buffer_minutes",
    "value": "2"
  }
]
```

Sample response:

```json
{
  "message": "Successfully updated 2 settings"
}
```

### D.4.11 Support Tickets

Description: Allows authenticated users to submit support tickets and authorized administrators to manage and reply to them.

HTTP methods and endpoints:

```http
POST /api/support/tickets
GET /api/admin/support/tickets
PUT /api/admin/support/tickets/{ticket_id}
POST /api/admin/support/tickets/{ticket_id}/replies
GET /api/admin/support/tickets/{ticket_id}/replies
```

Sample support-ticket request:

```json
{
  "subject": "Unable to record attendance",
  "description": "The camera captured my face but attendance was not recorded.",
  "category": "attendance",
  "priority": "medium"
}
```

Sample response:

```json
{
  "ticket_id": 5,
  "message": "Support ticket created successfully"
}
```

### D.4.12 Attendance Export

Description: Generates attendance reports for administrative review. The backend accepts filters for date range, class, student identifiers, attendance status, course, section, instructor, and output format.

HTTP method and endpoint:

```http
POST /api/admin/attendance/export
Content-Type: application/json
Authorization: Bearer <access_token>
```

Sample request:

```json
{
  "dateFrom": "2026-05-01",
  "dateTo": "2026-05-19",
  "courseCode": "CS101",
  "section": "A",
  "statusFilter": ["Present", "Late"],
  "exportFormat": "json"
}
```

Sample JSON response structure:

```json
{
  "report_title": "Attendance Report",
  "generated_at": "2026-05-19T10:00:00+08:00",
  "exported_by": "System Admin",
  "date_range": "2026-05-01 to 2026-05-19",
  "records": [
    {
      "student_id": "2025103001",
      "student_name": "Dela Cruz, Juan",
      "date": "2026-05-19",
      "time_in": "09:05:10",
      "status": "Present"
    }
  ],
  "class_summary": {
    "total_students": 1,
    "present_count": 1,
    "absent_count": 0,
    "late_count": 0,
    "excused_count": 0,
    "attendance_percentage": 100.0,
    "needs_attention": []
  }
}
```

Supported export formats in the backend are `json`, `csv`, `excel`, and `pdf`.

## D.5 Error Handling

The backend uses standard HTTP error responses through FastAPI exceptions for validation, authentication, authorization, and database errors. Common responses include:

| Status code | Meaning | Example cause |
|---:|---|---|
| 400 | Bad request | Missing parameter, invalid operation, invalid schedule JSON. |
| 401 | Unauthorized | Missing, invalid, or expired bearer token. |
| 403 | Forbidden | Authenticated user lacks the required permission. |
| 404 | Not found | User or other requested record does not exist. |
| 409 | Conflict | Duplicate student registration. |
| 500 | Internal server error | Database error, recognition processing error, or file-system write error. |

Sample unauthorized response:

```json
{
  "detail": "Invalid token"
}
```

Sample insufficient-permission response:

```json
{
  "detail": "Insufficient permissions: manage_users required"
}
```

## D.6 Not Applicable or Limited Items

The following items could not be documented as fully applicable based on the inspected backend code:

| Item | Applicability finding |
|---|---|
| Backend authentication for recognition | Not enforced on `/api/recognize` in the inspected FastAPI route. |
| Backend authentication for registration and capture | Not enforced on `/api/registration`, `/api/register`, or `/api/capture`. |
| Backend authentication for attendance retrieval | Not enforced on `/api/attendance`. |
| Backend authentication for room, course, student, instructor, class, and schedule lookup | Not enforced on the inspected lookup routes. |
| Persisted failed-recognition audit log | No dedicated table or endpoint was found for storing failed recognition attempts. The API returns failure responses, but failed attempts are not stored as structured records. |
| Recognition confidence or similarity in API response | The recognition code computes similarity internally for embedding comparison, but the public `RecognitionResponse` model does not expose confidence, distance, or similarity values. |
| Recognition duration in API response | No elapsed-time field is returned by `/api/recognize`. |
| Public debug endpoint for production use | `/api/debug/face-embedding-coverage-public` exists without authentication and is described in code as temporary/local verification. It should not be presented as a production administrative API. |

## D.7 Academic Summary

The FRAS backend API provides the operational interface between the Angular frontend, the attendance database, and the facial recognition subsystem. Its primary attendance workflow begins with student registration and face-image storage, proceeds through class-based facial recognition, validates the active schedule, assigns attendance status according to configurable timing thresholds, and writes attendance records to the database. Administrative APIs support user management, system configuration, analytics, support-ticket handling, and attendance report export.

The backend demonstrates role-based JWT authentication for administrative and support-management functions. However, several operational endpoints, including facial recognition and attendance retrieval, do not enforce backend authentication in the inspected implementation. This limitation should be considered when discussing deployment security and future system improvements.
