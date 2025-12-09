import sqlite3
import os
from backend import init_db

# Database path
DB_PATH = "attendance.db"

def seed_database():
    """Populate the database with sample Mapúa data for development/testing"""
    # Ensure database and tables exist
    init_db()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Clear FRAS-specific tables (attendance_logs, classes, enrollments) to start fresh
        # while keeping the migrated Mapúa data
        tables_to_clear = ['attendance_logs', 'classes', 'enrollments']
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"Cleared table: {table}")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    print(f"Table {table} does not exist, skipping clear.")
                else:
                    raise

        # Insert campuses
        cursor.execute("INSERT OR IGNORE INTO campuses (campus_name, location) VALUES (?, ?)", ('Mapúa Makati', 'Makati City'))
        cursor.execute("INSERT OR IGNORE INTO campuses (campus_name, location) VALUES (?, ?)", ('Mapúa Intramuros', 'Intramuros, Manila'))
        # Get campus_id for Makati
        cursor.execute("SELECT campus_id FROM campuses WHERE campus_name = ?", ('Mapúa Makati',))
        makati_campus_id = cursor.fetchone()[0]
        # Get campus_id for Intramuros
        cursor.execute("SELECT campus_id FROM campuses WHERE campus_name = ?", ('Mapúa Intramuros',))
        intramuros_campus_id = cursor.fetchone()[0]

        # Insert buildings
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('Main', makati_campus_id))
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('East', makati_campus_id))
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('West', makati_campus_id))
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('North', makati_campus_id))
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('South', makati_campus_id))
        # Get building_id for Main building
        cursor.execute("SELECT building_id FROM buildings WHERE building_name = ? AND campus_id = ?", ('Main', makati_campus_id))
        main_building_id = cursor.fetchone()[0]

        # Insert room types
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Lecture',))
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Laboratory',))
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Cisco',))

        # Create attendance_status_types table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_status_types (
            status_code TEXT PRIMARY KEY,
            status_name TEXT NOT NULL,
            description TEXT
        )
        """)

        # Insert attendance status types
        cursor.execute("INSERT OR IGNORE INTO attendance_status_types (status_code, status_name, description) VALUES (?, ?, ?)", ('present', 'Present', 'Student was present for the class'))
        cursor.execute("INSERT OR IGNORE INTO attendance_status_types (status_code, status_name, description) VALUES (?, ?, ?)", ('absent', 'Absent', 'Student was absent from the class'))
        cursor.execute("INSERT OR IGNORE INTO attendance_status_types (status_code, status_name, description) VALUES (?, ?, ?)", ('late', 'Late', 'Student arrived late to the class'))
        cursor.execute("INSERT OR IGNORE INTO attendance_status_types (status_code, status_name, description) VALUES (?, ?, ?)", ('excused', 'Excused Absence', 'Student had an approved absence'))

        # Create school_terms table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_terms (
            school_year TEXT,
            term INTEGER,
            start_date TEXT,
            end_date TEXT,
            PRIMARY KEY (school_year, term)
        )
        """)

        # Insert school terms for 2024-2025 (only if they don't already exist)
        school_terms = [
            ('2024-2025', 1, '2024-08-01', '2024-10-31'),
            ('2024-2025', 2, '2024-11-01', '2025-01-31'),
            ('2024-2025', 3, '2025-02-01', '2025-05-31')
        ]
        for school_year, term, start_date, end_date in school_terms:
            cursor.execute("SELECT COUNT(*) FROM school_terms WHERE school_year = ? AND term = ?", (school_year, term))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO school_terms (school_year, term, start_date, end_date) VALUES (?, ?, ?, ?)", 
                             (school_year, term, start_date, end_date))

        # Insert departments
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('DLA', 'Department of Liberal Arts'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('MATH', 'Mathematics'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('PHYS', 'Physics'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('ETYBSM', 'E.T. Yuchengco School Of Business And Management'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('SOIT', 'School of Information Technology'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('SOMDA', 'School of Multimedia and Digital Arts'))

        # Get department IDs for course insertion
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('DLA',))
        dla_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('MATH',))
        math_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('PHYS',))
        phys_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('ETYBSM',))
        etybsm_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('SOIT',))
        soit_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('SOMDA',))
        somda_dept_id = cursor.fetchone()[0]

        # Insert sample courses (at least 10 courses: 5 lectures, 3 labs, 1 cisco)
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED101', 'Understanding the Self', 3, dla_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED102', 'Readings in Philippine History', 3, dla_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED107', 'The Contemporary World', 3, dla_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('MATH101', 'College Algebra', 3, math_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('PHYS101', 'General Physics 1', 3, phys_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT119', 'Platform Technologies', 3, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS143-8', 'Object Oriented Programming', 3, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT135-8', 'Web Systems and Technologies', 3, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT166-1', 'Information Assurance and Security', 3, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS101L', 'Computer Programming 1 Lab', 1, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS102L', 'Computer Programming 2 Lab', 1, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT119L', 'Platform Technologies Lab', 1, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CIS101', 'Cisco Networking Fundamentals', 3, soit_dept_id))

        # Get room type IDs
        cursor.execute("SELECT room_type_id FROM room_types WHERE type_name = ?", ('Lecture',))
        lecture_type_id = cursor.fetchone()[0]
        cursor.execute("SELECT room_type_id FROM room_types WHERE type_name = ?", ('Laboratory',))
        lab_type_id = cursor.fetchone()[0]
        cursor.execute("SELECT room_type_id FROM room_types WHERE type_name = ?", ('Cisco',))
        cisco_type_id = cursor.fetchone()[0]

        # Insert sample rooms (3 rooms: 101 for lectures, 202 for lab, 303 for cisco)
        # Clear existing rooms and insert fresh data
        cursor.execute("DELETE FROM rooms")
        
        cursor.execute("INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('101', 1, makati_campus_id, main_building_id, lecture_type_id))
        cursor.execute("INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('202', 2, makati_campus_id, main_building_id, lab_type_id))
        cursor.execute("INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('303', 3, makati_campus_id, main_building_id, cisco_type_id))

        # Insert sample instructors (at least 10 instructors with numbers 2020103001 to 2020103010)
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103001', 'Smith', 'Jane', 'jane.smith@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103002', 'Johnson', 'John', 'john.johnson@mapua.edu.ph', dla_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103003', 'Williams', 'Emily', 'emily.williams@example.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103004', 'Brown', 'Michael', 'michael.brown@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103005', 'Davis', 'Sarah', 'sarah.davis@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103006', 'Miller', 'David', 'david.miller@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103007', 'Wilson', 'Lisa', 'lisa.wilson@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103008', 'Deveza', 'Eric', 'eric.deveza@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103009', 'Romance', 'Isaac', 'isaac.romance@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('2020103010', 'Santos', 'Maria', 'maria.santos@mapua.edu.ph', math_dept_id))

        # Insert sample admins
        cursor.execute("INSERT OR IGNORE INTO admins (employee_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('ADMIN001', 'Admin', 'Super', 'admin@mapua.edu.ph', soit_dept_id))

        # Insert sample students (at least 10 students with numbers 2025103001 to 2025103010)
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103001', 'Doe', 'John', 'john.doe@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103002', 'Smith', 'Jane', 'jane.smith@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103003', 'Johnson', 'Bob', 'bob.johnson@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103004', 'Williams', 'Alice', 'alice.williams@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103005', 'Brown', 'Charlie', 'charlie.brown@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103006', 'Davis', 'Emma', 'emma.davis@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103007', 'Miller', 'David', 'david.miller@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103008', 'Wilson', 'Sophia', 'sophia.wilson@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103009', 'Moore', 'James', 'james.moore@mapua.edu.ph'))
        cursor.execute("INSERT OR IGNORE INTO students (student_number, last_name, first_name, email) VALUES (?, ?, ?, ?)", ('2025103010', 'Taylor', 'Olivia', 'olivia.taylor@mapua.edu.ph'))

        # Insert sample class
        cursor.execute("INSERT INTO classes (course_id, instructor_id, room_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (1, 1, 1, 'A', 'MWF', '07:00', '08:00', 1))
        class_id = cursor.lastrowid

        # Enroll students 1-5 in this class
        for student_id in range(1, 6):
            cursor.execute("INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)", (student_id, class_id))

        # Seed permissions table
        permissions = [
            ('View personal schedule', 'schedule', 'Ability to view personal class schedule'),
            ('View attendance logs', 'attendance', 'Ability to view attendance logs'),
            ('Mark attendance using facial recognition', 'attendance', 'Ability to mark attendance using facial recognition'),
            ('Register new students', 'registration', 'Ability to register new students'),
            ('Create and manage user accounts', 'user_management', 'Ability to create and manage user accounts'),
            ('Edit room and schedule configurations', 'administration', 'Ability to edit room and schedule configurations'),
            ('Full system administration access', 'administration', 'Full system administration access'),
            ('View system analytics and reports', 'analytics', 'Ability to view system analytics and reports'),
            ('Manage system content and settings', 'content', 'Ability to manage system content and settings')
        ]

        for perm_name, category, description in permissions:
            cursor.execute("INSERT OR IGNORE INTO permissions (permission_name, description, category) VALUES (?, ?, ?)",
                         (perm_name, description, category))

        # Seed role_permissions table
        role_permissions = [
            ('instructor', 1),  # View personal schedule
            ('instructor', 2),  # View attendance logs
            ('instructor', 3),  # Mark attendance using facial recognition
            ('instructor', 4),  # Register new students
            ('it_admin', 1),    # View personal schedule
            ('it_admin', 2),    # View attendance logs
            ('it_admin', 3),    # Mark attendance using facial recognition
            ('it_admin', 4),    # Register new students
            ('it_admin', 5),    # Create and manage user accounts
            ('it_admin', 6),    # Edit room and schedule configurations
            ('it_admin', 8),    # View system analytics and reports
            ('super_admin', 1), # View personal schedule
            ('super_admin', 2), # View attendance logs
            ('super_admin', 3), # Mark attendance using facial recognition
            ('super_admin', 4), # Register new students
            ('super_admin', 5), # Create and manage user accounts
            ('super_admin', 6), # Edit room and schedule configurations
            ('super_admin', 7), # Full system administration access
            ('super_admin', 8), # View system analytics and reports
            ('super_admin', 9), # Manage system content and settings
        ]
        
        for role, perm_id in role_permissions:
            cursor.execute("INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)", (role, perm_id))

        # Seed system_settings table with default values
        system_settings = [
            ('system_name', 'FRAS - Facial Recognition Attendance System'),
            ('version', '1.0.0'),
            ('maintenance_mode', 'false'),
            ('max_upload_size', '10485760'),  # 10MB
            ('session_timeout', '3600'),  # 1 hour
            ('face_recognition_threshold', '0.6'),
            ('backup_frequency', 'daily'),
            ('log_retention_days', '90'),
            ('email_notifications', 'true')
        ]
        
        for setting_key, setting_value in system_settings:
            cursor.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", 
                         (setting_key, setting_value))

        # Create test users for each role
        # Note: Passwords are hashed versions of 'password123'
        test_users = [
            ('test.instructor@fras.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uAjhZzX8IwCe', 'instructor', 1),  # instructor_id = 1
            ('test.itadmin@fras.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uAjhZzX8IwCe', 'it_admin', 1),    # it_admin_id = 1
            ('test.superadmin@fras.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uAjhZzX8IwCe', 'super_admin', 1)  # super_admin_id = 1
        ]
        
        for email, password, role, ref_id in test_users:
            cursor.execute("INSERT OR IGNORE INTO users (email, password, role, reference_id) VALUES (?, ?, ?, ?)", 
                         (email, password, role, ref_id))

        # Create corresponding entries in role-specific tables if they don't exist
        # IT Admin
        cursor.execute("INSERT OR IGNORE INTO it_admins (employee_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", 
                     ('IT001', 'Test', 'Admin', 'test.itadmin@fras.com', 1))
        
        # Super Admin  
        cursor.execute("INSERT OR IGNORE INTO super_admins (employee_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", 
                     ('SUPER001', 'Test', 'SuperAdmin', 'test.superadmin@fras.com', 1))

        conn.commit()
        print("Mapúa database seeded successfully!")

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM departments")
        print(f"✓ Departments: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM courses")
        print(f"✓ Courses: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM instructors")
        print(f"✓ Instructors: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM students")
        print(f"✓ Students: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM rooms")
        print(f"✓ Rooms: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM campuses")
        print(f"✓ Campuses: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM buildings")
        print(f"✓ Buildings: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM school_terms")
        print(f"✓ School Terms: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM classes")
        print(f"✓ Classes: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM enrollments")
        print(f"✓ Enrollments: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM permissions")
        print(f"✓ Permissions: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM role_permissions")
        print(f"✓ Role Permissions: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"✓ Users: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        print(f"✓ System Settings: {cursor.fetchone()[0]}")

        print("\nNote: attendance_logs table is left empty for the FRAS system to populate.")
        print("Test accounts created:")
        print("  Instructor: test.instructor@fras.com / password123")
        print("  IT Admin: test.itadmin@fras.com / password123") 
        print("  Super Admin: test.superadmin@fras.com / password123")

if __name__ == "__main__":
    seed_database()