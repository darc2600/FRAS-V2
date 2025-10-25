import sqlite3

# Database path
DB_PATH = "attendance.db"

def seed_database():
    """Populate the database with sample data for development/testing"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Insert default campus
        cursor.execute("INSERT OR IGNORE INTO campuses (campus_name, location) VALUES (?, ?)", ('Mapúa Makati', 'Makati City'))
        # Get campus_id
        cursor.execute("SELECT campus_id FROM campuses WHERE campus_name = ?", ('Mapúa Makati',))
        campus_id = cursor.fetchone()[0]

        # Insert default building
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('Default Building', campus_id))
        # Get building_id
        cursor.execute("SELECT building_id FROM buildings WHERE building_name = ? AND campus_id = ?", ('Default Building', campus_id))
        building_id = cursor.fetchone()[0]

        # Insert room types
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Lecture',))
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Laboratory',))
        cursor.execute("INSERT OR IGNORE INTO room_types (type_name) VALUES (?)", ('Cisco',))

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
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('GED', 'General Education'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('CS', 'Computer Science'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('IT', 'Information Technology'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('SOIT', 'School of Information Technology'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('MATH', 'Mathematics'))
        cursor.execute("INSERT OR IGNORE INTO departments (dept_code, dept_name) VALUES (?, ?)", ('PHYS', 'Physics'))

        # Insert another building
        cursor.execute("INSERT OR IGNORE INTO buildings (building_name, campus_id) VALUES (?, ?)", ('Another Building', campus_id))
        cursor.execute("SELECT building_id FROM buildings WHERE building_name = ? AND campus_id = ?", ('Another Building', campus_id))
        building_id2 = cursor.fetchone()[0]

        # Get IDs
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('GED',))
        ged_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('CS',))
        cs_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('SOIT',))
        soit_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('MATH',))
        math_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT dept_id FROM departments WHERE dept_code = ?", ('PHYS',))
        phys_dept_id = cursor.fetchone()[0]
        cursor.execute("SELECT room_type_id FROM room_types WHERE type_name = ?", ('Lecture',))
        lecture_type_id = cursor.fetchone()[0]
        cursor.execute("SELECT room_type_id FROM room_types WHERE type_name = ?", ('Laboratory',))
        lab_type_id = cursor.fetchone()[0]

        # Insert sample rooms (1 lecture room and 1 lab room for testing)
        # Clear existing rooms and insert fresh data
        cursor.execute("DELETE FROM rooms")
        
        cursor.execute("INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('101', 1, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('201', 2, campus_id, building_id, lab_type_id))

        # Get room IDs for scheduling
        cursor.execute("SELECT room_id FROM rooms WHERE room_number = ?", ('101',))
        lecture_room_id = cursor.fetchone()[0]
        cursor.execute("SELECT room_id FROM rooms WHERE room_number = ?", ('201',))
        lab_room_id = cursor.fetchone()[0]

        # Get course IDs
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('GED101',))
        ged101_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('GED102',))
        ged102_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('GED107',))
        ged107_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('CS101',))
        cs101_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('CS102',))
        cs102_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('IT119',))
        it119_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('CS143-8',))
        cs143_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('IT135-8',))
        it135_id = cursor.fetchone()[0]
        cursor.execute("SELECT course_id FROM courses WHERE course_code = ?", ('IT166-1',))
        it166_id = cursor.fetchone()[0]

        # Insert sample instructors
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1001', 'Smith', 'Jane', 'jane.smith@example.com', cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1002', 'Johnson', 'John', 'john.johnson@example.com', ged_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1003', 'Williams', 'Emily', 'emily.williams@example.com', cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1004', 'Brown', 'Michael', 'michael.brown@example.com', cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1005', 'Davis', 'Sarah', 'sarah.davis@example.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1006', 'Miller', 'David', 'david.miller@example.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1007', 'Wilson', 'Lisa', 'lisa.wilson@example.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20051024', 'Deveza', 'Eric', 'eric.deveza@gmail.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20061401', 'Romance', 'Isaac', 'isaac.romance@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20080011', 'Santos', 'Maria', 'maria.santos@mapua.edu.ph', math_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20090022', 'Cruz', 'Jose', 'jose.cruz@mapua.edu.ph', phys_dept_id))

        # Get instructor IDs
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1001',))
        instructor_1001_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1002',))
        instructor_1002_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1003',))
        instructor_1003_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1004',))
        instructor_1004_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1005',))
        instructor_1005_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1006',))
        instructor_1006_id = cursor.fetchone()[0]
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_number = ?", ('1007',))
        instructor_1007_id = cursor.fetchone()[0]

        # Get term ID
        cursor.execute("SELECT term_id FROM school_terms WHERE school_year = ? AND term = ?", ('2024-2025', 1))
        term_id = cursor.fetchone()[0]

        # Insert sample class schedules with proper sections
        # Clear existing classes first
        cursor.execute("DELETE FROM classes")
        
        # Lecture Room Schedule (3-hour classes)
        # Monday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (ged101_id, lecture_room_id, instructor_1001_id, 'AM1', 'Monday', '07:00', '10:00', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs101_id, lecture_room_id, instructor_1002_id, 'BM1', 'Monday', '10:30', '13:30', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (ged102_id, lecture_room_id, instructor_1003_id, 'AM2', 'Monday', '14:00', '17:00', term_id))
        
        # Tuesday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs102_id, lecture_room_id, instructor_1004_id, 'BM2', 'Tuesday', '07:00', '10:00', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (ged107_id, lecture_room_id, instructor_1005_id, 'AM3', 'Tuesday', '10:30', '13:30', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it119_id, lecture_room_id, instructor_1006_id, 'BM3', 'Tuesday', '14:00', '17:00', term_id))
        
        # Wednesday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs143_id, lecture_room_id, instructor_1007_id, 'AM4', 'Wednesday', '07:00', '10:00', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it135_id, lecture_room_id, instructor_1001_id, 'BM4', 'Wednesday', '10:30', '13:30', term_id))
        
        # Thursday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it166_id, lecture_room_id, instructor_1002_id, 'AM5', 'Thursday', '07:00', '10:00', term_id))
        
        # Lab Room Schedule (4.5-hour classes)
        # Monday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs101_id, lab_room_id, instructor_1003_id, 'LAB1', 'Monday', '07:00', '11:30', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs102_id, lab_room_id, instructor_1004_id, 'LAB2', 'Monday', '13:00', '17:30', term_id))
        
        # Tuesday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it135_id, lab_room_id, instructor_1005_id, 'LAB3', 'Tuesday', '07:00', '11:30', term_id))
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cs143_id, lab_room_id, instructor_1006_id, 'LAB4', 'Tuesday', '13:00', '17:30', term_id))
        
        # Wednesday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it166_id, lab_room_id, instructor_1007_id, 'LAB5', 'Wednesday', '07:00', '11:30', term_id))
        
        # Thursday
        cursor.execute("INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (it119_id, lab_room_id, instructor_1001_id, 'LAB6', 'Thursday', '07:00', '11:30', term_id))

        conn.commit()
        print("Database seeded successfully!")

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM departments")
        print(f"✓ Departments: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM courses")
        print(f"✓ Courses: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM instructors")
        print(f"✓ Instructors: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM rooms")
        print(f"✓ Rooms: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM classes")
        print(f"✓ Classes: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM school_terms")
        print(f"✓ School Terms: {cursor.fetchone()[0]}")

if __name__ == "__main__":
    seed_database()