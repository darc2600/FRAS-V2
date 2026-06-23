# Appendix D: API Documentation for FRAS V2

This appendix documents the implemented API surface used by the final FRAS V2 professor-centered workflow. Evidence was extracted from `api/auth.py`, `v2/api.py`, `v2/models.py`, and `facial-attendance/src/app/api.service.ts`. Blackboard-ready CSV export is documented as a frontend-generated file export, not as direct Blackboard API synchronization.

## D.1 Authentication APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Authentication | POST | `/api/login` | Authenticates a user account and returns a bearer token plus user type and permissions. Used by the professor login workflow. | None | None | JSON: `email`, `password` | `access_token`, `token_type`, `user_type`, `permissions`, `user_id` | `api/auth.py`, `facial-attendance/src/app/api.service.ts` |
| Authentication | POST | `/login` | Backward-compatible alias for `/api/login`. | None | None | JSON: `email`, `password` | Same as `/api/login` | `api/auth.py` |

## D.2 Today's Classes APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Today's Classes | GET | `/api/v2/professors/{professor_id}/today/classes` | Loads the professor's classes for a target date and groups them into current, upcoming, and completed lists. | `professor_id` | Optional: `target_date` in `YYYY-MM-DD` format | None | `professor_id`, `date`, `current[]`, `upcoming[]`, `completed[]`; each class includes `class_id`, `course_code`, `course_name`, `section`, `room`, `day_of_week`, `start_time`, `end_time`, `student_count`, `status`, `active_session_id` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Today's Classes | GET | `/api/v2/professors/{professor_id}/schedule` | Loads all active classes assigned to the professor for schedule display. | `professor_id` | None | None | `professor_id`, `classes[]` with class/course/room/schedule/student-count fields | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Today's Classes | GET | `/api/v2/professors` | Lists professor summaries. Used by the frontend when professor context must be loaded. | None | None | None | `professor_id`, `user_id`, `faculty_number`, `professor_name`, `email`, `total_units`, `lecture_units`, `lab_units` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.3 Class Roster APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Class Roster | GET | `/api/v2/classes/{class_id}/students` | Loads the class roster, face profile status, recognition status, and attendance summary for each enrolled student. | `class_id` | None | None | `class_context`, `students[]`; student fields include `student_id`, `student_number`, `student_name`, `email`, `face_profile_status`, `recognition_status`, `attendance_rate`, `last_face_update`, `recognition_confidence`, session counts, `recent_history[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Class Roster | GET | `/api/v2/classes/{class_id}/students/{student_id}/history` | Loads the selected student's attendance history for a class. | `class_id`, `student_id` | None | None | `header`, `summary`, `records[]`; records include `session_id`, `session_date`, `scheduled_start`, `scheduled_end`, `attendance_status`, `presence_duration_minutes`, `outside_duration_minutes`, `break_count`, `system_assessment` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.4 Face Profile APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Face Profile | GET | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Loads student and class context before registering or updating a face profile. | `class_id`, `student_id` | None | None | `class_id`, `student_id`, `student_name`, `student_number`, `course_code`, `course_name`, `section`, `room`, `face_profile_status`, `last_face_update` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Face Profile | POST | `/api/v2/classes/{class_id}/students/{student_id}/face-profile` | Saves uploaded face profile image(s) and updates the student's face profile/embedding information. | `class_id`, `student_id` | None | Multipart form-data: `angles` as list of strings, `images` as list of uploaded files | `status`, `message`, `student_id`, `face_profile_status`, `saved_angles`, `image_paths` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.5 Live Session APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Live Session | POST | `/api/v2/classes/{class_id}/sessions/start` | Starts a live monitoring session for a class and creates session roster records. | `class_id` | None | JSON: `professor_id`, optional `session_date` | `session`, `roster[]`, `events[]`; session includes `session_id`, `class_id`, `professor_id`, schedule times, actual times, `session_status`, `student_record_count` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Live Session | GET | `/api/v2/sessions/{session_id}` | Loads session details, roster records, and attendance event timeline. | `session_id` | None | None | `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Live Session | POST | `/api/v2/sessions/{session_id}/events` | Creates a session event such as time-in, break-out, break-in, time-out, manual capture, missed recognition, or failure event. | `session_id` | None | JSON: `student_id`, `event_type`, optional `event_source`, optional `event_time`, optional `recognition_confidence`, optional `notes` | Updated `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Live Session | POST | `/api/v2/sessions/{session_id}/end` | Ends live monitoring and moves the session into post-session review. | `session_id` | None | Empty JSON object | `session`, `summary`, `roster[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.6 Manual Attendance APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Manual Attendance | POST | `/api/v2/sessions/{session_id}/manual-attendance` | Saves manual attendance for one or more students during live session or review. Supports `present`, `absent`, `late`, and `excused`. | `session_id` | None | JSON: `professor_id`, `records[]` with `record_id`, `student_id`, `status`; optional `notes`; optional `lock_status` | Updated `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.7 Facial Recognition APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Facial Recognition | POST | `/api/v2/classes/{class_id}/recognize` | Performs class-scoped face recognition using the uploaded image and active enrolled face embeddings. | `class_id` | None | Multipart form-data: `image` uploaded file | `status`, `message`, `student_id`, `student_name`, `confidence`, `decision_result`, `detected_face_count`, `best_match_score`, `second_best_match_score`, `recognition_threshold`, `match_margin`, `matched_embedding_id`, `matched_profile_id` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.8 Session Break APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Session Break | POST | `/api/v2/sessions/{session_id}/break/start` | Starts a session-wide break and changes the session state for Return Detection workflow. | `session_id` | None | Empty JSON object | Updated `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Session Break | POST | `/api/v2/sessions/{session_id}/break/end` | Ends the session-wide break after professor reauthentication. | `session_id` | None | JSON: `professor_email`, `password` | Updated `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.9 Return Detection APIs

Return Detection is not implemented as a separate backend endpoint. It is implemented by the frontend workflow during break mode using the same facial recognition and event creation APIs.

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Return Detection | POST | `/api/v2/classes/{class_id}/recognize` | Recognizes a returning student from a camera frame during break mode. | `class_id` | None | Multipart form-data: `image` | Recognition result fields including `student_id`, `student_name`, `confidence`, `decision_result` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `live-session.component.ts` |
| Return Detection | POST | `/api/v2/sessions/{session_id}/events` | Records the return event after recognition, typically as `break_in` with source `facial_recognition`. | `session_id` | None | JSON: `student_id`, `event_type`, `event_source`, optional `recognition_confidence`, optional `notes` | Updated `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `live-session.component.ts` |

## D.10 Post-Session Review APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Post-Session Review | GET | `/api/v2/sessions/{session_id}/review` | Loads post-session review summary and student records. | `session_id` | None | None | `session`, `summary`, `roster[]`; summary includes `present_count`, `late_count`, `partial_count`, `absent_count`, `excused_count`, `students_requiring_review`, `total_students`, `presence_validation_rate` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Post-Session Review | POST | `/api/v2/sessions/{session_id}/students/{student_id}/confirm` | Confirms a student's attendance record during professor review. | `session_id`, `student_id` | None | Empty JSON object | Updated review response: `session`, `summary`, `roster[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Post-Session Review | POST | `/api/v2/sessions/{session_id}/manual-attendance` | Saves override changes from post-session review mode. | `session_id` | None | JSON: `professor_id`, `records[]`, optional `notes`, `lock_status: true` | Updated session detail response | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `post-session-review.component.ts` |

## D.11 Student Evidence APIs

The Student Evidence page is frontend-composed from session review and session detail/event APIs. There is no separate backend endpoint named `/student-evidence`.

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Student Evidence | GET | `/api/v2/sessions/{session_id}/review` | Loads the student's session record from the review roster. | `session_id` | None | None | `session`, `summary`, `roster[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `student-evidence.component.ts` |
| Student Evidence | GET | `/api/v2/sessions/{session_id}` | Loads event timeline used to display student evidence. | `session_id` | None | None | `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `student-evidence.component.ts` |
| Student Evidence | POST | `/api/v2/sessions/{session_id}/students/{student_id}/confirm` | Confirms one student's status from the Student Evidence page. | `session_id`, `student_id` | None | Empty JSON object | Updated review response | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `student-evidence.component.ts` |
| Student Evidence | POST | `/api/v2/sessions/{session_id}/manual-attendance` | Saves Mark Excused or override action from the Student Evidence page. | `session_id` | None | JSON: `professor_id`, `records[]`, `lock_status`, `notes` | Updated session detail response | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `student-evidence.component.ts` |

## D.12 Professor Override and Mark Excused APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Professor Override | POST | `/api/v2/sessions/{session_id}/manual-attendance` | Applies professor override or Mark Excused by saving a locked manual attendance status. | `session_id` | None | JSON: `professor_id`, `records[]` with `record_id`, `student_id`, `status`; optional `notes`; `lock_status` often set to `true` for final review overrides | Updated `session`, `roster[]`, `events[]`; repository also records override evidence in `professor_overrides` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `student-evidence.component.ts`, `post-session-review.component.ts` |

## D.13 Finalization APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Finalization | POST | `/api/v2/sessions/{session_id}/finalize` | Finalizes the reviewed attendance session and enables CSV export in the frontend. | `session_id` | None | Empty JSON object | `session`, `summary`, `roster[]`; expected finalized session status in returned session data | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `post-session-review.component.ts` |

## D.14 Session History APIs

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| Session History | GET | `/api/v2/professors/{professor_id}/session-history` | Loads session history across a professor's classes. | `professor_id` | None | None | `class_context`, `summary`, `sessions[]`; session rows include `session_id`, `class_id`, `course_code`, `course_name`, `section`, `room`, `date`, `scheduled_start`, `scheduled_end`, `attendance_count`, `total_students`, `attendance_rate`, `average_presence_minutes`, `warning_count`, `excused_count`, `status` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Session History | GET | `/api/v2/classes/{class_id}/session-history` | Loads session history for a specific class. | `class_id` | None | None | `class_context`, `summary`, `sessions[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |

## D.15 CSV Export APIs

Blackboard-ready CSV export is frontend-only in the inspected V2 implementation. It is generated in the browser by `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` using review roster data. It should be described as Blackboard-ready CSV export, not direct Blackboard API synchronization.

| API group | HTTP method | Endpoint path | Purpose | Path parameters | Query parameters | Request body or form-data fields | Main response fields | Evidence source file |
|---|---|---|---|---|---|---|---|---|
| CSV Export | Frontend-only | No backend endpoint | Generates a Blackboard-ready CSV file after finalization. | Not applicable | Not applicable | Not applicable | CSV columns: `Student Number`, `Student Name`, `Attendance Status`; filename pattern includes course, section, session date, and session ID | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` |
| CSV Export supporting data | GET | `/api/v2/sessions/{session_id}/review` | Provides finalized roster data used by the frontend CSV export. | `session_id` | None | None | `session`, `summary`, `roster[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts` |
| Activity log CSV supporting data | GET | `/api/v2/sessions/{session_id}` | Provides event data used by the frontend activity log CSV export. | `session_id` | None | None | `session`, `roster[]`, `events[]` | `v2/api.py`, `v2/models.py`, `facial-attendance/src/app/api.service.ts`, `post-session-review.component.ts` |

## D.16 Sample API Requests and Responses

The following examples use safe placeholder values only.

### D.16.1 Login Request

```http
POST /api/login
Content-Type: application/json
```

```json
{
  "email": "<PROFESSOR_EMAIL>",
  "password": "<PASSWORD>"
}
```

Sample response:

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer",
  "user_type": "instructor",
  "permissions": ["mark_attendance", "view_attendance_logs"],
  "user_id": "<USER_ID>"
}
```

### D.16.2 Today's Classes Request

```http
GET /api/v2/professors/<PROFESSOR_ID>/today/classes?target_date=2026-06-17
Authorization: Bearer <JWT_TOKEN>
```

Sample response:

```json
{
  "professor_id": "<PROFESSOR_ID>",
  "date": "2026-06-17",
  "current": [
    {
      "class_id": "<CLASS_ID>",
      "course_code": "ITS131P",
      "course_name": "Sample Course",
      "section": "BM10",
      "room": "Room 101",
      "day_of_week": "Wednesday",
      "start_time": "10:30:00",
      "end_time": "14:00:00",
      "student_count": 40,
      "status": "current",
      "active_session_id": "<SESSION_ID>"
    }
  ],
  "upcoming": [],
  "completed": []
}
```

### D.16.3 Start Live Session Request

```http
POST /api/v2/classes/<CLASS_ID>/sessions/start
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "professor_id": "<PROFESSOR_ID>",
  "session_date": "2026-06-17"
}
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "class_id": "<CLASS_ID>",
    "professor_id": "<PROFESSOR_ID>",
    "scheduled_start": "2026-06-17T10:30:00",
    "scheduled_end": "2026-06-17T14:00:00",
    "actual_start": "2026-06-17T10:31:00",
    "actual_end": null,
    "session_status": "in_progress",
    "student_record_count": 40
  },
  "roster": [],
  "events": []
}
```

### D.16.4 Recognition Request

```http
POST /api/v2/classes/<CLASS_ID>/recognize
Content-Type: multipart/form-data
Authorization: Bearer <JWT_TOKEN>
```

Form-data:

| Field | Type | Example |
|---|---|---|
| `image` | File | `capture.jpg` |

Sample response:

```json
{
  "status": "success",
  "message": "Student recognized.",
  "student_id": "<STUDENT_ID>",
  "student_name": "Sample Student",
  "confidence": 91.25,
  "decision_result": "recognized",
  "detected_face_count": 1,
  "best_match_score": 0.9125,
  "second_best_match_score": 0.7201,
  "recognition_threshold": 0.7,
  "match_margin": 0.07,
  "matched_embedding_id": "<EMBEDDING_ID>",
  "matched_profile_id": "<FACE_PROFILE_ID>"
}
```

### D.16.5 Create Attendance Event Request

```http
POST /api/v2/sessions/<SESSION_ID>/events
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "student_id": "<STUDENT_ID>",
  "event_type": "break_in",
  "event_source": "facial_recognition",
  "event_time": "2026-06-17T11:15:00",
  "recognition_confidence": 91.25,
  "notes": "Return detection recognized the student."
}
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "session_status": "in_progress",
    "student_record_count": 40
  },
  "roster": [],
  "events": [
    {
      "event_id": "<EVENT_ID>",
      "session_id": "<SESSION_ID>",
      "student_id": "<STUDENT_ID>",
      "event_type": "break_in",
      "event_source": "facial_recognition",
      "recognition_confidence": 91.25,
      "is_voided": false
    }
  ]
}
```

### D.16.6 Manual Attendance / Mark Excused Request

```http
POST /api/v2/sessions/<SESSION_ID>/manual-attendance
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "professor_id": "<PROFESSOR_ID>",
  "records": [
    {
      "record_id": "<RECORD_ID>",
      "student_id": "<STUDENT_ID>",
      "status": "excused"
    }
  ],
  "notes": "Marked excused after professor review.",
  "lock_status": true
}
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "session_status": "under_review",
    "student_record_count": 40
  },
  "roster": [
    {
      "record_id": "<RECORD_ID>",
      "student_id": "<STUDENT_ID>",
      "student_number": "<STUDENT_NUMBER>",
      "student_name": "Sample Student",
      "final_status": "excused",
      "system_assessment": "valid_presence",
      "confirmed_by_professor": false
    }
  ],
  "events": []
}
```

### D.16.7 Session Break End Request

```http
POST /api/v2/sessions/<SESSION_ID>/break/end
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{
  "professor_email": "<PROFESSOR_EMAIL>",
  "password": "<PASSWORD>"
}
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "session_status": "in_progress",
    "student_record_count": 40
  },
  "roster": [],
  "events": []
}
```

### D.16.8 Post-Session Review Request

```http
GET /api/v2/sessions/<SESSION_ID>/review
Authorization: Bearer <JWT_TOKEN>
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "session_status": "under_review",
    "student_record_count": 40
  },
  "summary": {
    "present_count": 38,
    "late_count": 1,
    "partial_count": 0,
    "absent_count": 1,
    "excused_count": 0,
    "students_requiring_review": 2,
    "total_students": 40,
    "presence_validation_rate": 95.0
  },
  "roster": []
}
```

### D.16.9 Finalize Session Request

```http
POST /api/v2/sessions/<SESSION_ID>/finalize
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

```json
{}
```

Sample response:

```json
{
  "session": {
    "session_id": "<SESSION_ID>",
    "session_status": "finalized",
    "student_record_count": 40
  },
  "summary": {
    "present_count": 39,
    "late_count": 0,
    "partial_count": 0,
    "absent_count": 0,
    "excused_count": 1,
    "students_requiring_review": 0,
    "total_students": 40,
    "presence_validation_rate": 100.0
  },
  "roster": []
}
```

### D.16.10 Blackboard-Ready CSV Export

There is no backend API request for Blackboard CSV export in the inspected V2 workflow. The frontend generates the file after finalization.

| Item | Value |
|---|---|
| Implementation location | `facial-attendance/src/app/v2/pages/post-session-review/post-session-review.component.ts` |
| Export function | `exportBlackboardCsv()` |
| Filename function | `blackboardFilename()` |
| CSV row builder | `buildCsvRows(true)` |
| CSV columns | `Student Number`, `Student Name`, `Attendance Status` |
| Not a direct Blackboard API sync | Yes. It is a browser-side CSV download only. |
