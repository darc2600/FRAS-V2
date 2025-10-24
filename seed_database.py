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

        # Insert school terms for 2024-2025
        cursor.execute("INSERT OR IGNORE INTO school_terms (school_year, term, start_date, end_date) VALUES (?, ?, ?, ?)", ('2024-2025', 1, '2024-08-01', '2024-10-31'))
        cursor.execute("INSERT OR IGNORE INTO school_terms (school_year, term, start_date, end_date) VALUES (?, ?, ?, ?)", ('2024-2025', 2, '2024-11-01', '2025-01-31'))
        cursor.execute("INSERT OR IGNORE INTO school_terms (school_year, term, start_date, end_date) VALUES (?, ?, ?, ?)", ('2024-2025', 3, '2025-02-01', '2025-05-31'))

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

        # Insert sample rooms
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('101', 1, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('102', 1, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('201', 2, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('AM1', 1, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('AM2', 1, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('BM1', 2, campus_id, building_id, lecture_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('LAB1', 2, campus_id, building_id, lab_type_id))
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id) VALUES (?, ?, ?, ?, ?)", ('FOPM01', 3, campus_id, building_id2, lecture_type_id))

        # Insert sample courses
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED101', 'English 101', 3, ged_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED102', 'Mathematics 101', 3, ged_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('GED107', 'SOCIAL AND PROFESSIONAL ISSUES', 3, ged_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS101', 'Introduction to Programming', 3, cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS102', 'Data Structures', 3, cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT119', 'RESEARCH METHODS IN INFORMATION TECHNOLOGY', 3, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('CS143-8', 'HUMAN COMPUTER INTERACTION 2', 2, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT135-8', 'WEB SYSTEMS AND TECHNOLOGIES 2', 2, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT166-1', 'INFORMATION SECURITY AND ASSURANCE 2', 2, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('IT136', 'SOFTWARE QUALITY', 2, soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO courses (course_code, course_name, units, dept_id) VALUES (?, ?, ?, ?)", ('ITS164L', 'ADVANCED COMPUTER NETWORK 2', 2, soit_dept_id))

        # Insert sample instructors
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1001', 'Smith', 'Jane', 'jane.smith@example.com', cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1002', 'Johnson', 'John', 'john.johnson@example.com', ged_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('1003', 'Williams', 'Emily', 'emily.williams@example.com', cs_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20051024', 'Deveza', 'Eric', 'eric.deveza@gmail.com', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20061401', 'Romance', 'Isaac', 'isaac.romance@mapua.edu.ph', soit_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20080011', 'Santos', 'Maria', 'maria.santos@mapua.edu.ph', math_dept_id))
        cursor.execute("INSERT OR IGNORE INTO instructors (instructor_number, last_name, first_name, email, dept_id) VALUES (?, ?, ?, ?, ?)", ('20090022', 'Cruz', 'Jose', 'jose.cruz@mapua.edu.ph', phys_dept_id))

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
        cursor.execute("SELECT COUNT(*) FROM school_terms")
        print(f"✓ School Terms: {cursor.fetchone()[0]}")

if __name__ == "__main__":
    seed_database()