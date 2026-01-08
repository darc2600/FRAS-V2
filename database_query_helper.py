#!/usr/bin/env python3
"""
Database Query Helper - Face Path Verification
Useful SQL queries and Python helpers for debugging face registration issues
"""

import sqlite3
from services.db import get_connection

def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70)

def query_student_details(student_number):
    """Get full student details"""
    print_header(f"STUDENT DETAILS - {student_number}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_id, student_number, last_name, first_name, email,
               face_data_path, user_type, created_at, updated_at
        FROM students
        WHERE student_number = ?
    ''', (student_number,))
    
    result = cursor.fetchone()
    if result:
        sid, num, lname, fname, email, path, utype, created, updated = result
        print(f"Student ID:      {sid}")
        print(f"Student Number:  {num}")
        print(f"Name:            {fname} {lname}")
        print(f"Email:           {email}")
        print(f"User Type:       {utype}")
        print(f"face_data_path:  {path if path else '⚠️  NULL'}")
        print(f"Created:         {created}")
        print(f"Updated:         {updated}")
    else:
        print(f"❌ Student not found")
    
    conn.close()

def query_all_null_paths():
    """Find all students with NULL face_data_path"""
    print_header("STUDENTS WITH NULL face_data_path")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_id, student_number, last_name, first_name, face_data_path
        FROM students
        WHERE face_data_path IS NULL
        ORDER BY student_number
    ''')
    
    results = cursor.fetchall()
    if results:
        print(f"Found {len(results)} student(s) with NULL face_data_path:\n")
        for sid, num, lname, fname, path in results:
            print(f"  {num} - {fname} {lname} (ID: {sid})")
    else:
        print("✓ No students with NULL face_data_path")
    
    conn.close()

def query_enrollments(student_number):
    """Get student enrollments"""
    print_header(f"ENROLLMENTS - {student_number}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # First get student_id
    cursor.execute('SELECT student_id FROM students WHERE student_number = ?', (student_number,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ Student not found")
        conn.close()
        return
    
    student_id = result[0]
    
    # Get enrollments
    cursor.execute('''
        SELECT e.enrollment_id, e.student_id, e.class_id, 
               c.section, cr.course_code, cr.course_name
        FROM enrollments e
        JOIN classes c ON e.class_id = c.class_id
        JOIN courses cr ON c.course_id = cr.course_id
        WHERE e.student_id = ?
        ORDER BY cr.course_code
    ''', (student_id,))
    
    results = cursor.fetchall()
    if results:
        print(f"Found {len(results)} enrollment(s):\n")
        for eid, sid, cid, section, code, name in results:
            print(f"  [{eid}] {code} {section} - {name}")
    else:
        print("⚠️  No enrollments found")
    
    conn.close()

def query_statistics():
    """Get registration statistics"""
    print_header("REGISTRATION STATISTICS")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total students
    cursor.execute('SELECT COUNT(*) FROM students')
    total = cursor.fetchone()[0]
    
    # With face_data_path
    cursor.execute('SELECT COUNT(*) FROM students WHERE face_data_path IS NOT NULL')
    with_path = cursor.fetchone()[0]
    
    # NULL paths
    cursor.execute('SELECT COUNT(*) FROM students WHERE face_data_path IS NULL')
    null_path = cursor.fetchone()[0]
    
    # Average enrollments
    cursor.execute('''
        SELECT AVG(enrollment_count)
        FROM (
            SELECT COUNT(*) as enrollment_count
            FROM enrollments
            GROUP BY student_id
        )
    ''')
    avg_enrollments = cursor.fetchone()[0]
    
    print(f"Total Students:           {total}")
    print(f"With face_data_path:      {with_path} ({100*with_path//total if total else 0}%)")
    print(f"NULL face_data_path:      {null_path} ({100*null_path//total if total else 0}%)")
    print(f"Avg enrollments/student:  {avg_enrollments:.1f if avg_enrollments else 0}")
    
    conn.close()

def update_null_paths():
    """Fix NULL paths for students with existing dataset folders"""
    print_header("AUTO-FIX: UPDATE NULL face_data_path")
    
    import os
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all students with NULL paths
    cursor.execute('''
        SELECT student_id, student_number
        FROM students
        WHERE face_data_path IS NULL
    ''')
    
    results = cursor.fetchall()
    fixed = 0
    
    print(f"\nChecking {len(results)} student(s) with NULL paths...\n")
    
    for sid, num in results:
        dataset_path = os.path.join("dataset", num)
        if os.path.exists(dataset_path) and os.listdir(dataset_path):
            # Has data, update path
            cursor.execute('''
                UPDATE students
                SET face_data_path = ?
                WHERE student_id = ?
            ''', (dataset_path, sid))
            fixed += 1
            print(f"  ✓ Fixed {num}: {dataset_path}")
        else:
            print(f"  - Skip {num}: no dataset found")
    
    if fixed > 0:
        conn.commit()
        print(f"\n✓ Fixed {fixed} student(s)")
    else:
        print(f"\n- No students fixed")
    
    conn.close()

# Menu
def main():
    import sys
    
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  DATABASE QUERY HELPER - FACE PATH VERIFICATION".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\nAvailable queries:")
    print("  1. Student details (provide student number)")
    print("  2. All NULL paths")
    print("  3. Student enrollments (provide student number)")
    print("  4. Statistics")
    print("  5. Auto-fix NULL paths")
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "1" and len(sys.argv) > 2:
            query_student_details(sys.argv[2])
        elif cmd == "2":
            query_all_null_paths()
        elif cmd == "3" and len(sys.argv) > 2:
            query_enrollments(sys.argv[2])
        elif cmd == "4":
            query_statistics()
        elif cmd == "5":
            update_null_paths()
        else:
            print("\nUsage:")
            print("  python database_query_helper.py 1 <student_number>  - Student details")
            print("  python database_query_helper.py 2                   - All NULL paths")
            print("  python database_query_helper.py 3 <student_number>  - Enrollments")
            print("  python database_query_helper.py 4                   - Statistics")
            print("  python database_query_helper.py 5                   - Auto-fix NULL paths")
            print("\nExample:")
            print("  python database_query_helper.py 1 2025103006")
            print("  python database_query_helper.py 2")
            print("  python database_query_helper.py 4")
    else:
        print("\nUsage: python database_query_helper.py <command> [args]")
        print("\nExample:")
        print("  python database_query_helper.py 1 2025103006")
        print("  python database_query_helper.py 2")
        print("  python database_query_helper.py 4")

if __name__ == "__main__":
    main()
