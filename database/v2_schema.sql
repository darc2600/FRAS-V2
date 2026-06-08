-- FRAS V2 fresh PostgreSQL schema
-- Classroom Presence Monitoring System

DROP TABLE IF EXISTS blackboard_sync_logs CASCADE;
DROP TABLE IF EXISTS professor_overrides CASCADE;
DROP TABLE IF EXISTS attendance_events CASCADE;
DROP TABLE IF EXISTS student_session_records CASCADE;
DROP TABLE IF EXISTS attendance_sessions CASCADE;
DROP TABLE IF EXISTS attendance_status_types CASCADE;
DROP TABLE IF EXISTS student_face_profiles CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS professors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'professor',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE professors (
    professor_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(user_id),
    faculty_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    employment_status VARCHAR(100),
    total_units INT DEFAULT 0,
    lecture_units INT DEFAULT 0,
    lab_units INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(50) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    units INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    room_number VARCHAR(50) UNIQUE NOT NULL,
    floor_level INT,
    building VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    class_id INT NOT NULL REFERENCES classes(class_id),
    enrollment_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, class_id)
);

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

CREATE TABLE attendance_status_types (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

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

CREATE TABLE blackboard_sync_logs (
    sync_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES attendance_sessions(session_id) ON DELETE CASCADE,
    sync_status VARCHAR(50) DEFAULT 'pending',
    sync_message TEXT,
    synced_by_professor_id INT REFERENCES professors(professor_id),
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO attendance_status_types (status_name)
VALUES ('present'), ('late'), ('absent'), ('excused');

CREATE INDEX idx_classes_professor_day ON classes(professor_id, day_of_week);
CREATE INDEX idx_enrollments_class ON enrollments(class_id);
CREATE INDEX idx_attendance_sessions_class ON attendance_sessions(class_id);
CREATE INDEX idx_attendance_sessions_professor ON attendance_sessions(professor_id);
CREATE INDEX idx_student_session_records_session ON student_session_records(session_id);
CREATE INDEX idx_attendance_events_session_time ON attendance_events(session_id, event_time);
CREATE INDEX idx_attendance_events_student ON attendance_events(student_id);
