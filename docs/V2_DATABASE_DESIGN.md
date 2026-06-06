Final FRAS V2 Database
1. users

For login/authentication.

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'professor',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
2. professors

For professor profile and schedule ownership.

CREATE TABLE professors (
    professor_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(user_id),
    faculty_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
3. students
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    student_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    program VARCHAR(100),
    year_level VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
4. courses
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(50) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    units INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
5. rooms
CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    room_number VARCHAR(50) UNIQUE NOT NULL,
    floor_level INT,
    building VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
6. classes

This is the professor’s scheduled class.

CREATE TABLE classes (
    class_id SERIAL PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(course_id),
    professor_id INT NOT NULL REFERENCES professors(professor_id),
    room_id INT REFERENCES rooms(room_id),
    section VARCHAR(50) NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    term VARCHAR(50),
    academic_year VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
7. enrollments
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    class_id INT NOT NULL REFERENCES classes(class_id),
    enrollment_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, class_id)
);
8. student_face_profiles

For facial recognition registration.

CREATE TABLE student_face_profiles (
    face_profile_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    face_image_path TEXT,
    embedding_json JSONB,
    model_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
9. attendance_status_types
CREATE TABLE attendance_status_types (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

Seed values:

INSERT INTO attendance_status_types (status_name)
VALUES
('present'),
('late'),
('absent'),
('excused'),
('partial');
10. attendance_sessions

One actual class meeting.

CREATE TABLE attendance_sessions (
    session_id SERIAL PRIMARY KEY,
    class_id INT NOT NULL REFERENCES classes(class_id),
    professor_id INT NOT NULL REFERENCES professors(professor_id),

    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,

    session_status VARCHAR(50) DEFAULT 'not_started',
    session_timer_seconds INT DEFAULT 0,

    is_long_break BOOLEAN DEFAULT FALSE,
    long_break_minutes INT DEFAULT 0,

    finalized_at TIMESTAMP,
    synced_to_blackboard BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Recommended session_status values:

not_started
in_progress
on_break
ended
under_review
finalized
synced
cancelled
11. student_session_records

One student’s result for one session.

CREATE TABLE student_session_records (
    record_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES attendance_sessions(session_id) ON DELETE CASCADE,
    student_id INT NOT NULL REFERENCES students(student_id),

    final_status VARCHAR(50) DEFAULT 'absent',
    system_assessment VARCHAR(50) DEFAULT 'absent',

    time_in TIMESTAMP,
    time_out TIMESTAMP,

    total_presence_minutes INT DEFAULT 0,
    total_outside_minutes INT DEFAULT 0,
    break_count INT DEFAULT 0,

    late_minutes INT DEFAULT 0,
    requires_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,

    confirmed_by_professor BOOLEAN DEFAULT FALSE,
    confirmed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(session_id, student_id)
);

Recommended system_assessment values:

valid_presence
attendance_warning
requires_review
absent
12. attendance_events

This is the evidence table.

CREATE TABLE attendance_events (
    event_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES attendance_sessions(session_id) ON DELETE CASCADE,
    record_id INT REFERENCES student_session_records(record_id) ON DELETE CASCADE,
    student_id INT REFERENCES students(student_id),

    event_type VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_source VARCHAR(50) DEFAULT 'facial_recognition',

    recognition_confidence NUMERIC(5,2),
    notes TEXT,

    is_voided BOOLEAN DEFAULT FALSE,
    void_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Recommended event_type values:

time_in
break_out
break_in
time_out
manual_attendance
manual_capture
false_recognition
missed_recognition
camera_failure
network_failure

Recommended event_source values:

facial_recognition
manual_professor
system
13. professor_overrides
CREATE TABLE professor_overrides (
    override_id SERIAL PRIMARY KEY,
    record_id INT NOT NULL REFERENCES student_session_records(record_id) ON DELETE CASCADE,
    professor_id INT NOT NULL REFERENCES professors(professor_id),

    override_type VARCHAR(50) NOT NULL,
    previous_status VARCHAR(50),
    new_status VARCHAR(50),

    reason TEXT,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Recommended override_type values:

mark_excused
override_status
confirm_attendance
correct_time
void_event
add_manual_event
14. blackboard_sync_logs

Optional, but useful for your “future integration” claim.

CREATE TABLE blackboard_sync_logs (
    sync_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES attendance_sessions(session_id) ON DELETE CASCADE,

    sync_status VARCHAR(50) DEFAULT 'pending',
    sync_message TEXT,

    synced_by_professor_id INT REFERENCES professors(professor_id),
    synced_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

erDiagram

    USERS ||--o| PROFESSORS : owns
    PROFESSORS ||--o{ CLASSES : handles
    COURSES ||--o{ CLASSES : scheduled_as
    ROOMS ||--o{ CLASSES : hosts

    CLASSES ||--o{ ENROLLMENTS : contains
    STUDENTS ||--o{ ENROLLMENTS : enrolled_in

    STUDENTS ||--o{ STUDENT_FACE_PROFILES : has

    CLASSES ||--o{ ATTENDANCE_SESSIONS : has
    PROFESSORS ||--o{ ATTENDANCE_SESSIONS : starts

    ATTENDANCE_SESSIONS ||--o{ STUDENT_SESSION_RECORDS : contains
    STUDENTS ||--o{ STUDENT_SESSION_RECORDS : has

    ATTENDANCE_SESSIONS ||--o{ ATTENDANCE_EVENTS : records
    STUDENT_SESSION_RECORDS ||--o{ ATTENDANCE_EVENTS : supports
    STUDENTS ||--o{ ATTENDANCE_EVENTS : generates

    STUDENT_SESSION_RECORDS ||--o{ PROFESSOR_OVERRIDES : has
    PROFESSORS ||--o{ PROFESSOR_OVERRIDES : creates

    ATTENDANCE_SESSIONS ||--o{ BLACKBOARD_SYNC_LOGS : syncs
    PROFESSORS ||--o{ BLACKBOARD_SYNC_LOGS : performs

    USERS {
        int user_id PK
        string email UK
        text password_hash
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    PROFESSORS {
        int professor_id PK
        int user_id FK
        string faculty_number UK
        string first_name
        string last_name
        string email UK
        timestamp created_at
        timestamp updated_at
    }

    STUDENTS {
        int student_id PK
        string student_number UK
        string first_name
        string last_name
        string email
        string program
        string year_level
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    COURSES {
        int course_id PK
        string course_code UK
        string course_name
        int units
        timestamp created_at
        timestamp updated_at
    }

    ROOMS {
        int room_id PK
        string room_number UK
        int floor_level
        string building
        timestamp created_at
        timestamp updated_at
    }

    CLASSES {
        int class_id PK
        int course_id FK
        int professor_id FK
        int room_id FK
        string section
        string day_of_week
        time start_time
        time end_time
        string term
        string academic_year
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    ENROLLMENTS {
        int enrollment_id PK
        int student_id FK
        int class_id FK
        string enrollment_status
        timestamp created_at
        timestamp updated_at
    }

    STUDENT_FACE_PROFILES {
        int face_profile_id PK
        int student_id FK
        text face_image_path
        json embedding_json
        string model_name
        boolean is_active
        timestamp registered_at
        timestamp updated_at
    }

    ATTENDANCE_SESSIONS {
        int session_id PK
        int class_id FK
        int professor_id FK
        timestamp scheduled_start
        timestamp scheduled_end
        timestamp actual_start
        timestamp actual_end
        string session_status
        int session_timer_seconds
        boolean is_long_break
        int long_break_minutes
        timestamp finalized_at
        boolean synced_to_blackboard
        timestamp synced_at
        timestamp created_at
        timestamp updated_at
    }

    STUDENT_SESSION_RECORDS {
        int record_id PK
        int session_id FK
        int student_id FK
        string final_status
        string system_assessment
        timestamp time_in
        timestamp time_out
        int total_presence_minutes
        int total_outside_minutes
        int break_count
        int late_minutes
        boolean requires_review
        text review_reason
        boolean confirmed_by_professor
        timestamp confirmed_at
        timestamp created_at
        timestamp updated_at
    }

    ATTENDANCE_EVENTS {
        int event_id PK
        int session_id FK
        int record_id FK
        int student_id FK
        string event_type
        timestamp event_time
        string event_source
        decimal recognition_confidence
        text notes
        boolean is_voided
        text void_reason
        timestamp created_at
    }

    PROFESSOR_OVERRIDES {
        int override_id PK
        int record_id FK
        int professor_id FK
        string override_type
        string previous_status
        string new_status
        text reason
        text notes
        timestamp created_at
    }

    BLACKBOARD_SYNC_LOGS {
        int sync_id PK
        int session_id FK
        string sync_status
        text sync_message
        int synced_by_professor_id FK
        timestamp synced_at
        timestamp created_at
    }