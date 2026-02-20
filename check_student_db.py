import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check if student 2025103006 exists
cursor.execute('SELECT student_id, student_number, last_name, first_name, face_data_path FROM students WHERE student_number = ?', ('2025103006',))
result = cursor.fetchone()
print('Student 2025103006:', result)

if result:
    student_id = result[0]
    face_data_path = result[4]
    print(f'Face data path in DB: {face_data_path}')
    
    # Check enrollments
    cursor.execute('''
        SELECT e.class_id, c.course_id, c.section, co.course_code 
        FROM enrollments e
        JOIN classes c ON e.class_id = c.class_id
        JOIN courses co ON c.course_id = co.course_id
        WHERE e.student_id = ?
    ''', (student_id,))
    enrollments = cursor.fetchall()
    print(f'Enrollments: {enrollments}')

# Check all students
print('\nFirst 15 students:')
cursor.execute('SELECT student_number, face_data_path FROM students LIMIT 15')
for row in cursor.fetchall():
    print(row)

conn.close()
