# FRAS V2 Mermaid Diagrams for Thesis

These diagrams are based on the implemented V2 professor-centered workflow in the repository, especially:

- `facial-attendance/src/app/app.routes.ts`
- `facial-attendance/src/app/api.service.ts`
- `v2/api.py`
- `v2/service.py`
- `v2/repository.py`
- `v2/models.py`
- `services/face_embeddings.py`
- `database/v2_schema.sql`
- `docker-compose.v2.yml`
- `Dockerfile.backend.v2`
- `facial-attendance/Dockerfile.v2`
- `facial-attendance/nginx.v2.conf`

## 1. FRAS V2 System Architecture Diagram

Supported by Angular/Ionic frontend routes and API client, FastAPI V2 routes, V2 service/repository layers, DeepFace embedding helpers, PostgreSQL schema, and Docker/Nginx deployment files.

```mermaid
flowchart LR
    Professor["Professor"]

    subgraph Frontend["Frontend Container"]
        Browser["Professor Browser"]
        Angular["Angular / Ionic V2 App"]
        Pages["V2 Professor Pages<br/>Today's Classes<br/>Class Roster<br/>Face Profile<br/>Live Session<br/>Post-Session Review<br/>Student Evidence<br/>Session History"]
        ApiClient["Angular ApiService"]
    end

    subgraph Nginx["Nginx Runtime"]
        Static["Serves Angular Build"]
        Proxy["Proxies /api to Backend"]
    end

    subgraph Backend["Backend Container"]
        Uvicorn["Uvicorn ASGI Server"]
        FastAPI["FastAPI Application"]
        V2Router["V2 API Router<br/>/api/v2"]
        AuthRouter["Auth Router<br/>/api/login"]
        Service["V2AttendanceService<br/>Business Rules"]
        Repository["V2AttendanceRepository<br/>Database Access"]
        Recognition["Face Embedding Service<br/>DeepFace + OpenCV/Image Processing"]
    end

    subgraph Data["Data Layer"]
        PostgreSQL["PostgreSQL Database"]
        FaceProfiles["Face Profile Image Paths"]
        Embeddings["Student Face Embeddings"]
    end

    subgraph Docker["Docker Compose Runtime"]
        FrontendContainer["frontend"]
        BackendContainer["backend"]
        DbContainer["db postgres:16-alpine"]
        Volumes["dataset and data volumes"]
    end

    Professor --> Browser
    Browser --> Angular
    Angular --> Pages
    Pages --> ApiClient
    ApiClient --> Nginx
    Static --> Angular
    Nginx --> Proxy
    Proxy --> Uvicorn
    Uvicorn --> FastAPI
    FastAPI --> AuthRouter
    FastAPI --> V2Router
    V2Router --> Service
    Service --> Repository
    Service --> Recognition
    Repository --> PostgreSQL
    Recognition --> FaceProfiles
    Recognition --> Embeddings
    Embeddings --> PostgreSQL
    FaceProfiles --> PostgreSQL

    Docker --> FrontendContainer
    Docker --> BackendContainer
    Docker --> DbContainer
    Docker --> Volumes
    FrontendContainer --> Nginx
    BackendContainer --> Backend
    DbContainer --> PostgreSQL
```

## 2. V2 Database ERD

Supported by `database/v2_schema.sql`, the `student_face_embeddings` helper table in `services/face_embeddings.py`, and V2 repository queries.

```mermaid
erDiagram
    users ||--o| professors : "has professor profile"
    professors ||--o{ classes : "teaches"
    courses ||--o{ classes : "offered as"
    rooms ||--o{ classes : "assigned to"
    classes ||--o{ enrollments : "has"
    students ||--o{ enrollments : "enrolled in"

    students ||--o{ student_face_profiles : "has"
    students ||--o{ student_face_embeddings : "has"
    classes ||--o{ attendance_sessions : "has sessions"
    professors ||--o{ attendance_sessions : "conducts"

    attendance_sessions ||--o{ student_session_records : "creates records"
    students ||--o{ student_session_records : "has session record"

    attendance_sessions ||--o{ attendance_events : "records events"
    student_session_records ||--o{ attendance_events : "supports evidence"
    students ||--o{ attendance_events : "appears in events"

    student_session_records ||--o{ professor_overrides : "may be overridden"
    professors ||--o{ professor_overrides : "records override"

    attendance_sessions ||--o{ blackboard_sync_logs : "may log CSV sync/export status"

    users {
        int user_id PK
        string email
        string password_hash
        string role
        boolean is_active
    }

    professors {
        int professor_id PK
        int user_id FK
        string faculty_number
        string first_name
        string last_name
        string email
    }

    students {
        int student_id PK
        string student_number
        string first_name
        string last_name
        string email
        boolean is_active
    }

    courses {
        int course_id PK
        string course_code
        string course_name
        int units
    }

    rooms {
        int room_id PK
        string room_number
        int floor_level
        string building
    }

    classes {
        int class_id PK
        int course_id FK
        int professor_id FK
        int room_id FK
        string section
        string day_of_week
        time start_time
        time end_time
        boolean is_active
    }

    enrollments {
        int enrollment_id PK
        int student_id FK
        int class_id FK
        string enrollment_status
    }

    student_face_profiles {
        int face_profile_id PK
        int student_id FK
        string face_image_path
        json embedding_json
        string model_name
        boolean is_active
    }

    student_face_embeddings {
        int embedding_id PK
        int student_id
        string model_name
        text embedding_json
        string source_image_path
    }

    attendance_sessions {
        int session_id PK
        int class_id FK
        int professor_id FK
        datetime scheduled_start
        datetime scheduled_end
        datetime actual_start
        datetime actual_end
        string session_status
        datetime finalized_at
    }

    student_session_records {
        int record_id PK
        int session_id FK
        int student_id FK
        string final_status
        string system_assessment
        datetime time_in
        datetime time_out
        int total_presence_minutes
        int total_outside_minutes
        int break_count
        int late_minutes
        boolean confirmed_by_professor
    }

    attendance_events {
        int event_id PK
        int session_id FK
        int record_id FK
        int student_id FK
        string event_type
        datetime event_time
        string event_source
        number recognition_confidence
        string notes
    }

    professor_overrides {
        int override_id PK
        int record_id FK
        int professor_id FK
        string override_type
        string previous_status
        string new_status
        string reason
    }

    blackboard_sync_logs {
        int sync_id PK
        int session_id FK
        string sync_status
        string sync_message
        int synced_by_professor_id FK
        datetime synced_at
    }
```

## 3. API Communication Diagram

Supported by V2 professor-facing Angular routes/API methods and V2 backend endpoints in `v2/api.py`.

```mermaid
sequenceDiagram
    actor Professor
    participant UI as Angular V2 Professor UI
    participant API as FastAPI Backend
    participant Service as V2AttendanceService
    participant DB as PostgreSQL
    participant Recognition as DeepFace Embedding Service
    participant CSV as Browser CSV Download

    Professor->>UI: Login
    UI->>API: POST /api/login
    API->>DB: Verify user credentials
    DB-->>API: Professor user
    API-->>UI: JWT and user type

    UI->>API: GET /api/v2/professors/{id}/today/classes
    API->>Service: Load today's classes
    Service->>DB: Query professor classes and active sessions
    DB-->>Service: Class cards
    Service-->>UI: Today's Classes

    UI->>API: GET /api/v2/classes/{class_id}/students
    API->>Service: Load class roster
    Service->>DB: Query enrollments, face status, attendance history
    DB-->>Service: Roster data
    Service-->>UI: Class roster

    UI->>API: GET /api/v2/classes/{class_id}/students/{student_id}/face-profile
    API->>Service: Load face profile context
    Service->>DB: Query student and face profile
    DB-->>Service: Face profile status
    Service-->>UI: Face profile page data

    UI->>API: POST /api/v2/classes/{class_id}/students/{student_id}/face-profile
    API->>Service: Save face profile images
    Service->>Recognition: Extract face embeddings
    Recognition-->>Service: Embedding vectors
    Service->>DB: Store active face profile and embedding
    DB-->>Service: Save confirmation
    Service-->>UI: Face profile saved

    UI->>API: POST /api/v2/classes/{class_id}/sessions/start
    API->>Service: Start live session
    Service->>DB: Create attendance session and student records
    DB-->>Service: Session detail
    Service-->>UI: Live session screen

    UI->>API: POST /api/v2/sessions/{session_id}/manual-attendance
    API->>Service: Save manual attendance
    Service->>DB: Apply status and professor override
    Service-->>UI: Updated session detail

    UI->>API: POST /api/v2/classes/{class_id}/recognize
    API->>Service: Recognize face
    Service->>Recognition: Extract embedding and compare
    Recognition-->>Service: Match decision
    Service-->>UI: Recognized student or warning

    UI->>API: POST /api/v2/sessions/{session_id}/events
    API->>Service: Create attendance event
    Service->>DB: Insert time_in, break_in, break_out, or time_out event
    Service->>DB: Recalculate student record
    Service-->>UI: Updated roster and events

    UI->>API: POST /api/v2/sessions/{session_id}/break/start
    API->>Service: Start session break
    Service->>DB: Set session on_break and create break_out events
    Service-->>UI: Return Detection Mode

    UI->>API: POST /api/v2/sessions/{session_id}/break/end
    API->>Service: Verify professor password and end break
    Service->>DB: Set session in_progress
    Service-->>UI: Resume live session

    UI->>API: POST /api/v2/sessions/{session_id}/end
    API->>Service: End session
    Service->>DB: Set actual_end and under_review
    Service->>DB: Add system time_out events and recalculate records
    Service-->>UI: Post-session review

    UI->>API: GET /api/v2/sessions/{session_id}/review
    API->>Service: Load review
    Service->>DB: Query records and summary
    Service-->>UI: Review data

    UI->>API: POST /api/v2/sessions/{session_id}/students/{student_id}/confirm
    API->>Service: Confirm student record
    Service->>DB: Mark confirmed_by_professor
    Service-->>UI: Updated review

    UI->>API: POST /api/v2/sessions/{session_id}/finalize
    API->>Service: Finalize attendance
    Service->>DB: Confirm records and set finalized
    Service-->>UI: Finalized review

    UI->>CSV: Export Blackboard-ready CSV
    CSV-->>Professor: Download CSV file

    UI->>API: GET /api/v2/professors/{id}/session-history
    API->>Service: Load session history
    Service->>DB: Query finalized and review sessions
    Service-->>UI: Session history
```

## 4. Recognition Workflow Diagram

Supported by `recognizeV2Face()` in the frontend API service, `/api/v2/classes/{class_id}/recognize`, `V2AttendanceService.recognize_face_for_class`, and `services/face_embeddings.py`.

```mermaid
flowchart TD
    A["Camera frame captured in Live Session UI"] --> B["POST image to /api/v2/classes/{class_id}/recognize"]
    B --> C["FastAPI V2 recognition endpoint"]
    C --> D["Save upload to temporary image file"]
    D --> E["Read recognition settings<br/>model and threshold"]
    E --> F["DeepFace.represent extracts face embedding"]
    F --> G{Face detected?}

    G -- "No" --> H["Return no_face_recognized"]
    G -- "Yes" --> I["Use first detected face embedding"]

    I --> J["Load active enrolled embeddings<br/>for the class and model"]
    J --> K["Validate enrolled students only<br/>via enrollments and active face profiles"]
    K --> L["Compute cosine similarity<br/>against stored student embeddings"]
    L --> M["Sort candidates by similarity"]
    M --> N{Best score >= threshold?}

    N -- "No" --> O["Return below_threshold"]
    N -- "Yes" --> P{Top match clear by margin?}

    P -- "No" --> Q["Return ambiguous_match"]
    P -- "Yes" --> R["Return recognized student<br/>with confidence percent"]

    R --> S["Frontend decides attendance action"]
    S --> T["POST /api/v2/sessions/{session_id}/events"]
    T --> U["Create time_in or break_in event"]
    U --> V["Recalculate student session record"]
    V --> W["Update live roster and evidence timeline"]
```

## 5. Session Lifecycle / State Diagram

Supported by `start_session`, `start_break`, `end_break`, `end_session`, `finalize_session`, and `confirm_student_record` in `v2/service.py`.

```mermaid
stateDiagram-v2
    [*] --> NotStarted: Professor selects class

    NotStarted --> InProgress: Start Session
    InProgress --> InProgress: Facial Recognition Time In
    InProgress --> InProgress: Manual Attendance
    InProgress --> InProgress: Student Break Out or Break In

    InProgress --> OnBreak: Start Session Break
    OnBreak --> OnBreak: Return Detection Mode
    OnBreak --> OnBreak: Facial Recognition Break In
    OnBreak --> InProgress: End Break with professor password

    InProgress --> UnderReview: End Session
    OnBreak --> UnderReview: End Session closes open timelines
    UnderReview --> UnderReview: Review student evidence
    UnderReview --> UnderReview: Confirm student record
    UnderReview --> UnderReview: Professor override or mark excused

    UnderReview --> Finalized: Finalize Attendance
    InProgress --> Finalized: Finalize also ends session if needed
    OnBreak --> Finalized: Finalize also ends session if needed

    Finalized --> CSVReady: Blackboard-ready CSV export enabled
    CSVReady --> SessionHistory: Session visible in history
    SessionHistory --> [*]
```

## 6. End Session and Time Out Workflow Diagram

Supported by `end_session`, `_close_open_student_timelines`, `_recalculate_student_record`, `finalize_session`, `create_event`, and `update_student_record`.

```mermaid
flowchart TD
    A["Professor clicks End Session"] --> B["POST /api/v2/sessions/{session_id}/end"]
    B --> C["Load session"]
    C --> D{Session status valid?<br/>in_progress, on_break, or under_review}

    D -- "No" --> E["Reject request"]
    D -- "Yes" --> F["Set actual_end timestamp"]
    F --> G["Set session status to under_review"]
    G --> H["Load roster records"]

    H --> I{"For each student:<br/>last active event?"}

    I -- "time_in, break_in, or manual_attendance" --> J["Create system time_out event<br/>at actual_end"]
    I -- "break_out" --> K["Create system time_out event<br/>note: student was outside when session ended"]
    I -- "already time_out or no open timeline" --> L["No new time_out needed"]

    J --> M["Recalculate record"]
    K --> M
    L --> M

    M --> N["Update time_in and time_out"]
    N --> O["Compute presence minutes"]
    O --> P["Compute outside minutes"]
    P --> Q["Compute break count and late minutes"]
    Q --> R["Update final_status and system_assessment"]
    R --> S{"More students?"}

    S -- "Yes" --> I
    S -- "No" --> T["Return post-session review"]
    T --> U["Professor reviews, confirms, or overrides"]
    U --> V["Finalize Attendance"]
    V --> W["CSV export becomes available"]
```

## 7. Blackboard-ready CSV Export Flow

Supported by `post-session-review.component.ts` methods `finalizeAttendance`, `exportBlackboardCsv`, `buildCsvRows`, `blackboardStatusLabel`, `blackboardFilename`, and `downloadCsv`. This is CSV export only; direct Blackboard API integration is not implemented.

```mermaid
flowchart TD
    A["Post-Session Review Page"] --> B["Professor reviews attendance"]
    B --> C{"Session finalized?"}

    C -- "No" --> D["POST /api/v2/sessions/{session_id}/finalize"]
    D --> E["Backend confirms records<br/>and sets session finalized"]
    E --> F["Frontend reloads finalized review"]

    C -- "Yes" --> F
    F --> G["Export Blackboard CSV button enabled"]

    G --> H["Build CSV rows in browser"]
    H --> I["Columns:<br/>Student Number<br/>Student Name<br/>Attendance Status"]
    I --> J["Map final_status to Blackboard-ready label<br/>Present, Late, Excused, or Absent"]
    J --> K["Generate filename<br/>fras_blackboard_{class}_{date}_session-{id}.csv"]
    K --> L["Create text/csv Blob"]
    L --> M["Download CSV file"]

    M --> N["Professor uses CSV for Blackboard encoding/import preparation"]

    N --> O["No direct Blackboard API integration claimed"]
```
