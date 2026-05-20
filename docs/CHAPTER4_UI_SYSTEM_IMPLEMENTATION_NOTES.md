# Chapter 4 UI And System Implementation Notes

This document summarizes the implemented FRAS modules in a form that can be adapted for Chapter 4 of the capstone paper. The focus is on what each interface does, how it interacts with the backend, and what system logic is executed behind the visible UI.

## 1. Login Page Implementation

### Module Purpose

The login page provides the authentication entry point of the FRAS system. It verifies the user through an email-and-password form, receives the authenticated user profile from the backend, stores the session details on the client side, and redirects the user to the attendance monitoring page after successful login.

### Authentication Workflow

The login workflow begins when the user enters an email address and password in the Angular login form. The `LoginComponent` first checks whether both fields are present. If either field is missing, the interface displays the validation message `Email and password required` and does not send a request to the backend.

When both fields are provided, the component calls `LoginService.login()`, which sends a POST request to `/api/login` with the email and password as JSON data. The backend endpoint in `api/auth.py` receives the login request, searches the database for the matching account, validates the password, checks whether the account is active, loads the user permissions, and generates a JWT access token.

After the backend returns a successful response, the frontend builds a user object containing the email, user type, user ID, token, and permissions. This object is passed to `AuthService.login()`, which stores the session data in `localStorage` and updates the current user state using a `BehaviorSubject`. The login page then redirects the user to `/monitor`.

### JWT Handling

The backend uses PyJWT to generate a signed access token. The token payload includes the user email, user type, permissions, user ID, and expiration time. On the frontend, the token is stored under `authToken` in `localStorage` together with the user type, user ID, email, and permissions.

Authenticated frontend requests are handled by `AuthInterceptor`, which retrieves the saved token from `AuthService` and attaches it to outgoing requests as:

```text
Authorization: Bearer <token>
```

Protected backend endpoints decode and validate the token using the configured JWT secret and algorithm. If the token is expired or invalid, the backend returns an unauthorized response.

### Role-Based Access

Role-based access is implemented on both the frontend and backend. On the frontend, route guards check the current user before allowing navigation:

| Guard | Purpose |
|---|---|
| `AuthGuard` | Allows access only to authenticated users. |
| `AdminGuard` | Allows access to IT admin and super admin users. |
| `AnalyticsGuard` | Allows access to users with analytics or all-data permissions. |
| `SuperAdminGuard` | Allows access only to super admin users. |

The backend uses permission dependencies such as `require_admin_permission()` to protect administrative API routes. Super administrators are granted full access, while other user types are checked against their assigned permission list.

### Validation And Security Behavior

The frontend performs basic required-field validation before login. The backend performs the actual security checks, including account lookup, password verification, active-account validation, permission loading, and JWT generation. Password verification supports hashed passwords through Passlib and also preserves compatibility with existing plain password records when present in the database.

If the credentials are invalid, the backend returns an unauthorized response and the frontend displays the error message from the backend. If an account is deactivated, the backend rejects the login attempt.

### Frontend And Backend Interaction

| Step | Frontend Behavior | Backend Behavior |
|---|---|---|
| 1 | User enters email and password. | No backend action yet. |
| 2 | Login form validates required fields. | No backend action if fields are missing. |
| 3 | `LoginService` posts credentials to `/api/login`. | Backend receives and validates credentials. |
| 4 | Frontend receives token and user details. | Backend returns JWT, user type, permissions, and user ID. |
| 5 | `AuthService` stores session data in `localStorage`. | Backend waits for future bearer-token requests. |
| 6 | Router redirects user to `/monitor`. | Protected endpoints validate JWT on later requests. |

### Capstone-Ready Paragraph

The login module was implemented as the security entry point of FRAS. The Angular frontend validates the email and password fields before sending the credentials to the FastAPI backend through the `/api/login` endpoint. The backend verifies the account, checks whether the user is active, validates the password, loads the assigned permissions, and generates a JWT access token. The frontend stores the token and user profile in local storage and uses an HTTP interceptor to attach the token to protected API requests. Route guards enforce role-based access on the client side, while backend permission dependencies protect administrative endpoints. After successful authentication, the user is redirected to the attendance monitoring page.

## 2. Attendance Monitor Implementation

### Module Purpose

The attendance monitor is the main operational interface for recording student attendance through facial recognition. It allows the instructor to select a floor, room, and course-section, capture a student face image through the webcam, submit the image for recognition, and view the attendance log for the selected class on the current Manila date.

### Recognition Workflow

When the attendance monitor loads, it retrieves available floors from the backend. After the user selects a floor, the frontend loads the rooms for that floor. After a room is selected, the frontend retrieves the course-section combinations assigned to that room. Each course-section entry includes the class ID required by the recognition endpoint.

The instructor captures an image through the webcam. The component converts the captured base64 image into a `Blob`, wraps it as a `File`, and sends it to `/api/recognize` as multipart form data together with the selected `class_id`. The backend passes the file and class ID to the recognition service and repository.

The recognition repository temporarily saves the submitted image, extracts its face embedding, loads stored embeddings for students enrolled in the selected class, and compares the submitted face against enrolled students using cosine similarity. If a match is found, the backend verifies the class schedule and computes the attendance status.

### Manual And Automatic Recognition

The attendance monitor supports both manual and automatic recognition behavior.

Manual recognition is triggered when the instructor clicks `Capture & Mark Attendance` or presses the spacebar. The frontend captures one frame from the webcam and immediately submits it for recognition.

Automatic recognition is controlled by the `Start Auto Recognition` and `Stop Auto Recognition` button. When enabled, the frontend triggers a webcam snapshot every two seconds. The component also keeps the last recognized student ID and timestamp so the UI can avoid repeatedly showing the same recognition result within a short 10-second window. The backend still performs the more authoritative duplicate attendance prevention using the configured attendance buffer.

### Attendance Validation

The backend does not record attendance immediately after face matching. It first validates whether the selected class exists and whether the current Manila day and time match the class schedule. If the class is scheduled on a different day or the current time is outside the class period, the backend returns a failed response explaining that attendance recognition is not valid for the current time.

If the schedule is valid, the backend computes how many minutes have passed since the class started. It uses system settings to classify the attendance record as Present, Late, or Absent. The default setting behavior supports a present threshold, a late threshold, and an absent threshold.

### Schedule Verification

Schedule verification is performed by querying the selected class record from the database using `class_id`. The backend reads the class day, start time, and end time. It compares these values with the current date and time in the `Asia/Manila` timezone. This prevents attendance from being recorded for the wrong day, wrong time, or invalid class schedule.

### Duplicate Attendance Prevention

Duplicate prevention is implemented in both the frontend and backend, but the backend is the main source of enforcement. The frontend avoids repeated auto-recognition messages for the same student within 10 seconds. The backend checks the `attendance_logs` table for the most recent attendance record of the same student in the same class on the same date. If the latest record is within the configured attendance buffer period, the backend does not insert another record and returns a message indicating that attendance was already recorded.

### Frontend And Backend Interaction

| Step | Frontend Behavior | Backend Behavior |
|---|---|---|
| 1 | Load floors, rooms, and course-section options. | Returns room and class selection data. |
| 2 | Instructor selects class context. | No recognition yet. |
| 3 | Webcam captures image manually or automatically. | No backend action until submission. |
| 4 | Image is converted into a file and sent to `/api/recognize`. | Receives multipart image and class ID. |
| 5 | UI waits for recognition result. | Extracts embedding and compares against enrolled students. |
| 6 | UI displays success or failure message. | Validates schedule, computes status, prevents duplicates, and records attendance. |
| 7 | UI refreshes the attendance table. | `/api/attendance` returns logs for the selected course-section and date. |

### Recognition Engine Integration

The recognition engine uses DeepFace and helper functions from `services/face_embeddings.py`. Registered student face images are processed into embeddings and stored in the database. During recognition, the submitted face image is also converted into an embedding, then compared against enrolled student embeddings. If embedding-based comparison succeeds, the backend uses the matched student ID to build the attendance response. If needed, the repository can fall back to direct DeepFace image-to-image verification against stored student face images.

### Capstone-Ready Paragraph

The attendance monitor module was implemented as the primary attendance recording interface of FRAS. The interface allows the instructor to select a floor, room, and course-section before capturing a student image through the webcam. The captured image is converted into a file and submitted to the backend recognition endpoint together with the selected class ID. The backend extracts the face embedding, compares it against enrolled student embeddings, validates the class schedule using Manila time, determines whether the student is Present, Late, or Absent, and prevents duplicate records using a configurable attendance buffer. The frontend then displays the recognition result and refreshes the attendance log for the selected class and date.

## 3. User Management Implementation

### Module Purpose

The user management module provides administrative control over FRAS accounts. It allows authorized users to view account records, search and filter the user directory, create new users, change user roles, reset passwords, delete accounts, and perform bulk activation, deactivation, or deletion operations.

### RBAC Handling

Role-based access control is enforced through permissions from the authenticated user profile. The frontend displays or hides controls depending on permissions such as `manage_users` and `reset_passwords`. For example, create, delete, bulk operation, and role modification controls are only shown to users with the appropriate permissions. Password reset buttons are shown only to users who can reset passwords.

The backend protects user management endpoints using `require_admin_permission()`. Endpoints such as `/api/admin/users`, `/api/admin/reset-password`, and `/api/admin/users/bulk` require the appropriate permission before executing the requested operation. Super administrators automatically pass these permission checks, while other roles are validated against their permission list.

### User Creation And Editing

The create-user workflow is handled through the `UserManagementComponent`. The form requires an email, password, and user type. It also validates that passwords are at least six characters long. For administrative account types such as IT admin and super admin, the frontend requires an employee number.

When the form is submitted, the frontend sends the new account details to `/api/admin/users`. The backend creates the corresponding user record and associated role profile when necessary. After successful creation, the frontend clears the form, hides the create-user panel, reloads the user list, and displays a success message.

Role editing is handled through a role dropdown in the user table. The component tracks each user’s original role and only sends an update if a role change is pending. The frontend also checks whether the current user is allowed to modify the selected role. Super administrators can perform broader role changes, while IT administrators are more limited.

### Password Reset Workflow

Password reset is available from the user management table and from the separate password reset component. In the user table, an administrator can enter a new password for a selected user. The frontend validates that the new password has at least six characters before sending the reset request to `/api/admin/reset-password`.

The password reset endpoint is protected by the `reset_passwords` permission. The backend updates the selected user’s stored password and returns a success response. The frontend then displays confirmation to the administrator.

### Filtering And Search

The user management interface includes client-side filtering and search. Administrators can search by email or full name, filter by user type, and filter by active or inactive status. The component applies the filters to the loaded user list and sorts the result by user type and name. The interface also shows how many filters are currently active and allows the administrator to clear all filters.

### Admin Permissions And Bulk Operations

Bulk operations are available when one or more users are selected. The module supports bulk activation, bulk deactivation, and bulk deletion. Before executing a bulk action, the frontend asks for confirmation. The selected user IDs and operation type are sent to `/api/admin/users/bulk`, where the backend performs the requested operation after verifying the `manage_users` permission.

### API Interactions

| Function | Frontend Method | Backend Endpoint |
|---|---|---|
| Load users | `getUsers()` | `GET /api/admin/users` |
| Create user | `createUser()` | `POST /api/admin/users` |
| Update user | `updateUser()` | `PUT /api/admin/users/{user_id}` |
| Delete user | `deleteUser()` | `DELETE /api/admin/users/{user_id}` |
| Reset password | `resetPassword()` | `POST /api/admin/reset-password` |
| Bulk operation | `bulkUserOperation()` | `POST /api/admin/users/bulk` |

### Capstone-Ready Paragraph

The user management module was implemented to support administrative account control within FRAS. The interface retrieves user records from the backend and allows administrators to search, filter, create, update, delete, and perform bulk operations on user accounts. Access to user management functions is controlled by role-based permissions, so sensitive actions such as creating users, changing roles, resetting passwords, and deleting accounts are only available to authorized administrators. The backend reinforces these controls through permission-protected endpoints, ensuring that administrative actions are validated before database changes are applied.

## 4. Support Ticket Implementation

### Module Purpose

The support ticket module provides a structured way for users to request assistance and for administrators to manage system issues. It includes a user-facing ticket submission page and an administrative ticket management interface.

### Ticket Lifecycle

The ticket lifecycle begins when an authorized user opens the support form and submits a subject, category, priority, and description. The frontend validates that all required fields are filled in before sending the request to `/api/support/tickets`. The backend stores the ticket in the `support_tickets` table with the submitting user ID, category, priority, default status, and creation timestamp.

Administrators access the ticket management page to view submitted tickets. They can filter tickets by status or priority, select a ticket to view its details, update the ticket status or priority, and add replies. The lifecycle statuses supported by the system are:

| Status | Meaning |
|---|---|
| `open` | Ticket has been submitted and is awaiting action. |
| `in_progress` | Ticket is being reviewed or handled by an administrator. |
| `resolved` | The issue has been addressed. |
| `closed` | The ticket has been completed or archived. |

### Priority And Status Handling

Ticket priority is selected by the submitting user and can be updated by administrators. The supported priority values are low, medium, high, and critical. The admin interface visually distinguishes priorities and statuses using badge styles, making urgent or unresolved tickets easier to scan.

The backend supports filtering ticket queries using optional status and priority parameters. This allows the admin interface to request only the tickets that match the selected filter criteria.

### Replies

Ticket replies are stored separately from the main ticket record in the `ticket_replies` table. Each reply contains the ticket ID, user ID, message, internal flag, and creation timestamp. Administrators can add replies to a selected ticket, and the frontend reloads the reply list after successful submission.

The reply form includes an `is_internal` option. This allows the system to distinguish between normal replies and internal administrative notes. The ticket record is also updated when a reply is added so the ticket’s update timestamp reflects ongoing activity.

### Admin Workflow

The admin support workflow starts by loading tickets through `/api/admin/support/tickets`. The administrator can filter by status and priority, click a ticket to open its details, review the description and metadata, update the status or priority, and add replies. The interface displays success and error messages after update and reply operations.

Access to the support management page is permission-gated. The admin interface checks for `manage_support`, and the backend uses permission checks before allowing support ticket management actions.

### Database Interaction

Support tickets use two main tables:

| Table | Purpose |
|---|---|
| `support_tickets` | Stores ticket subject, description, category, priority, status, submitting user, assigned user, and timestamps. |
| `ticket_replies` | Stores reply messages associated with support tickets. |

The support ticket schema includes indexes for user ID, status, priority, assigned administrator, creation timestamp, ticket replies, and reply creation timestamp. This improves lookup performance for common administrative queries.

### API Interactions

| Function | Frontend Method | Backend Endpoint |
|---|---|---|
| Submit ticket | `submitSupportTicket()` | `POST /api/support/tickets` |
| Load tickets | `getSupportTickets()` | `GET /api/admin/support/tickets` |
| Update ticket | `updateSupportTicket()` | `PUT /api/admin/support/tickets/{ticket_id}` |
| Load replies | `getTicketReplies()` | `GET /api/admin/support/tickets/{ticket_id}/replies` |
| Add reply | `addTicketReply()` | `POST /api/admin/support/tickets/{ticket_id}/replies` |

### Capstone-Ready Paragraph

The support ticket module was implemented to provide an organized communication channel between FRAS users and system administrators. Authorized users can submit support requests by selecting a category and priority and describing the issue. The backend stores each request as a support ticket with a default lifecycle status. Administrators can view tickets, filter them by status or priority, update their progress, and add replies or internal notes. The module uses separate database tables for tickets and replies, allowing each issue to maintain a clear history of administrative actions and communication.

## 5. Student Registration And Face Enrollment Implementation

### Module Purpose

The student registration module enrolls students into the facial attendance workflow. It captures identifying information, validates the student number against existing records, allows the user to add course-section schedule entries, captures multiple face images from guided angles, and submits the registration data and images to the backend.

### Student Validation Workflow

The registration form requires the student ID, last name, first name, and email. Before the student can submit face data, the component validates the student number by calling the backend student lookup API. If the student number exists, the module stores the expected student record but does not automatically fill personal details for privacy. When the user enters the last name, first name, or email, the frontend checks the entered value against the expected database value and displays validation errors if the values do not match.

### Guided Face Capture

The module uses the browser camera through `navigator.mediaDevices.getUserMedia()`. It guides the user to capture multiple facial angles: Center, Left, Right, Up, and Down. A registration cannot be submitted until all required angles are captured. The captured images are stored as browser `Blob` objects with preview URLs before submission.

### Schedule And Enrollment Handling

The student schedule portion allows the user to add one or more course-section entries. Course codes are assisted by autocomplete suggestions loaded from the backend course list. Duplicate course-section entries are blocked on the frontend. When submitted, the schedule entries are serialized as JSON and sent with the student information and face images.

### Backend Processing

The frontend sends a multipart form request to `/api/registration`. The backend parses the student data, schedule JSON, and uploaded face images. It creates or updates the student record, links the student to matching classes through enrollments, saves images under the dataset folder, updates the student face data path, extracts a face embedding, and stores the embedding in the `student_face_embeddings` table.

### Capstone-Ready Paragraph

The student registration module was implemented to connect student records with the facial recognition attendance process. The interface validates the student number against existing records, checks whether the entered personal information matches the expected student data, guides the user through multiple face-angle captures, and requires at least one course-section schedule entry before submission. The frontend sends the student details, schedule entries, and captured face images to the backend using multipart form data. The backend saves the images, updates the student record, creates enrollment records, and generates a face embedding that is later used during attendance recognition.

## 6. Attendance Logs Implementation

### Module Purpose

The attendance logs module allows authorized users to retrieve and review attendance records by course, section, and date. It supports both single-date viewing and date-range viewing, groups records by date, displays attendance statuses, and provides a CSV export for the currently displayed records.

### Filtering Workflow

When the page loads, it initializes the date filter to the current Manila date and loads valid courses from the backend. Users can type or select a course through autocomplete suggestions. After a course is selected, the frontend requests the available sections for that course. The user then chooses a section and selects either a single date or a date range before searching the logs.

### Backend Interaction

The component calls `/api/attendance` through `ApiService.getAttendance()`, passing the course code, section, and date filters. The backend resolves the course and class, joins attendance logs with student and status data, and returns a list of attendance entries. The frontend maps the returned array values into student number, student name, timestamp, and status fields.

### CSV Export

The module supports client-side CSV export. If logs are available, the component builds a CSV file with student number, name, date, time, and status. The generated filename includes the course, section, and selected date or date range.

### Capstone-Ready Paragraph

The attendance logs module was implemented to allow users to retrieve attendance records using course, section, and date filters. The interface loads valid courses and sections from the backend, supports single-date and date-range search modes, and groups retrieved logs by Manila date. The backend returns attendance data from the attendance log, student, class, course, and status tables. The frontend displays the records with status styling and allows the user to export the filtered result as a CSV file for offline review.

## 7. Room Schedule And Schedule Editor Implementation

### Module Purpose

The room schedule module displays the weekly schedule assigned to a room, while the room schedule editor allows authorized administrators to create, edit, undo, save, or delete schedule entries. These modules support the attendance monitor because recognition depends on valid room, class, course, and schedule data.

### Schedule Viewing

The room schedule viewer uses a weekly grid composed of fixed time slots and days from Monday to Sunday. When a room number is entered, the frontend calls `/api/room-schedule/{room_id}`. The returned schedule entries are placed into the correct day and time-slot cells. If no entries are found, the interface displays a no-schedule message.

### Schedule Editing

The schedule editor provides a grid-based editing interface. Administrators enter a room, course code, section, and professor. The component loads valid courses and instructor names from the backend and uses autocomplete suggestions for both course and instructor fields. Before a cell can be filled, the frontend validates that the course exists and that the professor name matches a known instructor.

The editor tracks changes in an action history so the latest change can be undone. It also stores the original grid, allowing all unsaved changes to be reverted. When saving, the grid is flattened into schedule entries containing course code, section, professor, day, start time, and end time. These entries are sent to `/api/room-schedule/{room_id}`.

### Delete Protection

Schedule deletion uses a confirmation modal. The administrator must type `DELETE` before the frontend calls the delete endpoint. This prevents accidental removal of a room schedule.

### Capstone-Ready Paragraph

The room schedule modules were implemented to manage the class schedule information used by the attendance workflow. The schedule viewer displays room assignments in a weekly time-slot grid, while the schedule editor allows administrators to fill, clear, undo, revert, save, and delete schedule entries. The editor validates course and instructor data against backend records before allowing schedule entries to be saved. This ensures that the attendance monitor receives valid class and room data when instructors select a class for facial recognition attendance.

## 8. System Settings Implementation

### Module Purpose

The system settings module allows the super administrator to configure operational behavior of the FRAS system. Settings include facial recognition parameters, attendance thresholds, image processing values, performance options, security/privacy settings, user experience settings, hardware-related settings, and general system configuration.

### Settings Organization

The frontend loads settings from `/api/admin/system-settings` and groups them by category. Categories include Facial Recognition, Attendance Logic, Image Processing, Performance, Security and Privacy, User Experience, Hardware and Devices, System Configuration, Branding, and General Configuration.

### Pending Changes Workflow

Changes are staged locally before they are saved. When a user edits a setting, the component compares the new value with the current value and places modified settings into a `pendingChanges` object. The interface can show how many settings are pending and display a confirmation modal listing the old and new values. When confirmed, the component sends all pending changes in one bulk request to `/api/admin/system-settings/bulk`.

### Validation And Automation

Number settings are validated against configured minimum and maximum values before being staged. The module also provides a control for manually triggering automatic absent marking through `/api/admin/mark-automatic-absents`. This connects system configuration directly to attendance automation.

### Capstone-Ready Paragraph

The system settings module was implemented to give the super administrator control over configurable recognition and attendance behavior. Settings are loaded from the backend, grouped by category, and edited through type-aware controls such as boolean toggles, number inputs, select fields, and text inputs. Changes are staged first and saved in bulk only after confirmation. These settings directly affect recognition thresholds, attendance classification, duplicate buffers, automatic absent marking, and other operational rules of the system.

## 9. Analytics Dashboard Implementation

### Module Purpose

The analytics dashboard provides administrative insight into system usage, attendance activity, and face registration readiness. It summarizes student and instructor totals, attendance record counts, recent attendance activity, monthly trends, attendance status distribution, top classes by attendance logs, and face embedding coverage.

### Data Loading

The dashboard uses `forkJoin()` to load analytics data and face embedding coverage at the same time. It calls `/api/admin/analytics` for dashboard metrics and `/api/admin/face-embedding-coverage` for face registration readiness. If either request fails, the interface displays an error message.

### Visual Analytics

The frontend converts backend data into cards, bar charts, progress bars, and a face-readiness donut indicator. Monthly student registrations, instructor registrations, and attendance records are shown as January-to-December bar charts. Attendance status breakdown and top classes are shown using progress-list visuals. Face readiness is computed from the number of students with face data compared with the total number of students.

### Capstone-Ready Paragraph

The analytics module was implemented to provide administrators with a visual summary of system activity and readiness. It retrieves dashboard metrics and face embedding coverage from the backend, then presents the results through summary cards, monthly bar charts, status breakdowns, class activity indicators, and face registration completion metrics. This helps administrators monitor whether the system has sufficient registered face data and whether attendance records are being generated as expected.

## 10. Attendance Reports Implementation

### Module Purpose

The attendance reports module generates formal attendance reports for classes or professors. It supports report previews in the page and exports in CSV, Excel, and PDF formats. It also includes advanced filters for students and attendance statuses.

### Report Types

The module supports two report modes:

| Report Type | Purpose |
|---|---|
| Class Report | Generates attendance records and summary statistics for one selected class. |
| Professor Report | Generates consolidated attendance reports for classes handled by a selected professor. |

### Form Validation

The report form requires a date range and report type. If the report type is class, a class must be selected. If the report type is professor, a professor must be selected. The component also validates that the start date is not later than the end date.

### Export Workflow

For preview mode, the component sends a JSON report request to the backend and renders the returned report data on the page. For CSV, Excel, and PDF exports, it sends the same filter data as a file request and downloads the returned blob using a generated filename. The backend endpoints used are `/api/admin/attendance/export` and `/api/admin/attendance/export/professor`.

### Capstone-Ready Paragraph

The attendance reports module was implemented to support formal review and export of attendance data. Administrators can generate either class-based reports or professor-based consolidated reports using date ranges and optional filters for students and attendance status. Reports can be previewed in the interface or exported as CSV, Excel, or PDF files. The backend aggregates attendance records, computes class summaries, and returns either structured report data or downloadable files depending on the selected export format.

## 11. Navigation And Permission-Aware Layout Implementation

### Module Purpose

The navigation module controls which pages are visible to each user based on their role and permissions. It improves usability by showing only the functions that the logged-in user is allowed to access.

### Permission-Based Menu Handling

The navbar subscribes to the current user state from `AuthService`. When the user changes, the navbar reads the user permissions and sets flags for each feature area, including attendance monitoring, logs, student registration, room schedule viewing, schedule editing, user management, password reset, system configuration, analytics, reports, support submission, and support management.

The sidebar/profile component also provides sign-out behavior. On logout, `AuthService` clears the stored session data and routes the user back to the login page.

### Capstone-Ready Paragraph

The navigation layer was implemented as a permission-aware interface that adapts to the logged-in user. After authentication, the navbar reads the user's permission list and displays only the modules that the user is allowed to access. This supports the role-based design of the system by reducing unauthorized navigation paths and keeping the interface focused on each user's responsibilities.

## 12. Legacy And Supporting Modules

### Account Registration

The `registration` route provides a simple email-and-password registration form that posts to the user registration endpoint. It validates that email and password are present and checks that the password contains at least one uppercase letter, number, or special character. This module is separate from the student face enrollment workflow and is mainly a basic account registration path.

### Password Reset Page

The password reset page provides a focused interface for administrators to reset a user password. It validates that an email address is entered, calls `/api/admin/reset-password`, and displays success or error feedback. This workflow is also available from the user management table.

### Schedule Upload

The schedule upload component is a supporting or legacy module that allows a student number and image file to be submitted to `/api/upload-schedule-image`. The active backend route was not identified in the current API scan, so this module should be described cautiously as a supporting or experimental schedule-upload feature unless the endpoint is restored or confirmed in deployment.

### Webcam Capture

The standalone webcam capture component provides a simpler image capture and attendance marking workflow. It loads rooms and course-section options, captures a webcam image, converts it into a file, and posts it to `/api/recognize`. The main production attendance workflow is represented more completely by the Attendance Monitor module.

## 13. Module Coverage Checklist

The Chapter 4 implementation notes now cover the following implemented system areas:

| System Area | Covered In This Document |
|---|---|
| Login and JWT authentication | Yes |
| Role-based access control and route guards | Yes |
| Permission-aware navigation | Yes |
| Attendance monitor and recognition workflow | Yes |
| Manual and automatic recognition | Yes |
| Recognition engine integration | Yes |
| Student registration and face enrollment | Yes |
| Attendance logs and CSV export | Yes |
| Room schedule viewing | Yes |
| Room schedule editing and deletion | Yes |
| User management | Yes |
| Password reset | Yes |
| System settings | Yes |
| Analytics dashboard | Yes |
| Attendance report generation and export | Yes |
| User support ticket submission | Yes |
| Admin support ticket management | Yes |
| Legacy/simple account registration | Yes |
| Supporting/legacy schedule upload | Yes, with caveat |
| Standalone webcam capture | Yes, as supporting module |

## 14. Suggested Chapter 4 Writing Structure

For Chapter 4, each UI module can be written using the following pattern:

1. Interface purpose: describe what the page is used for.
2. User workflow: explain what the user does step by step.
3. Validation: describe required fields and error handling.
4. Backend interaction: identify the API endpoints used.
5. Business logic: explain the system rules executed behind the page.
6. Security: identify route guards, permissions, and protected endpoints.
7. Output: describe what the system displays or stores after completion.

This structure makes the implementation sound like a completed system instead of a simple description of screens.
