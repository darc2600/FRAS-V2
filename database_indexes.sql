-- Database Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number);
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_class ON enrollments(student_id, class_id);
CREATE INDEX IF NOT EXISTS idx_classes_course_section ON classes(course_id, section);
CREATE INDEX IF NOT EXISTS idx_classes_room_day_time ON classes(room_id, day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_attendance_logs_class_date ON attendance_logs(class_id, DATE(timestamp));
CREATE INDEX IF NOT EXISTS idx_attendance_logs_student_date ON attendance_logs(student_id, DATE(timestamp));
CREATE INDEX IF NOT EXISTS idx_attendance_logs_status ON attendance_logs(status_id);
CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_instructors_number ON instructors(instructor_number);