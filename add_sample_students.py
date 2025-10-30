#!/usr/bin/env python3
"""
Add sample students to test the attendance system
"""
import sqlite3

def add_sample_students():
    """Add sample students for testing"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # Sample students
    students = [
        ('STU001', 'Doe', 'John', 'john.doe@student.edu'),
        ('STU002', 'Smith', 'Jane', 'jane.smith@student.edu'),
        ('STU003', 'Johnson', 'Bob', 'bob.johnson@student.edu'),
        ('STU004', 'Williams', 'Alice', 'alice.williams@student.edu'),
        ('STU005', 'Brown', 'Charlie', 'charlie.brown@student.edu'),
    ]

    print("Adding sample students...")

    for student_number, last_name, first_name, email in students:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO students (student_number, last_name, first_name, email)
                VALUES (?, ?, ?, ?)
            ''', (student_number, last_name, first_name, email))
            print(f"✓ Added student: {student_number} - {first_name} {last_name}")
        except sqlite3.Error as e:
            print(f"✗ Error adding {student_number}: {e}")

    # Enroll students in classes
    print("\nEnrolling students in classes...")

    # Get GED101-AM1 class
    cursor.execute('''
        SELECT c.class_id FROM classes c
        JOIN courses co ON c.course_id = co.course_id
        WHERE co.course_code = ? AND c.section = ?
    ''', ('GED101', 'AM1'))

    class_result = cursor.fetchone()
    if class_result:
        class_id = class_result[0]

        # Get all student IDs
        cursor.execute('SELECT student_id FROM students')
        student_ids = [row[0] for row in cursor.fetchall()]

        # Enroll each student in the class
        for student_id in student_ids:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO enrollments (student_id, class_id)
                    VALUES (?, ?)
                ''', (student_id, class_id))
                print(f"✓ Enrolled student {student_id} in class {class_id}")
            except sqlite3.Error as e:
                print(f"✗ Error enrolling student {student_id}: {e}")
    else:
        print("✗ GED101-AM1 class not found")

    conn.commit()
    conn.close()
    print("\nSample students added successfully!")

if __name__ == "__main__":
    add_sample_students()