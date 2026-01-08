#!/usr/bin/env python3
"""
Debug script to check face data registration for student 2025103006
This script will verify:
1. Database entries for the student
2. Face data directory and files
3. face_data_path value in database
"""

import sqlite3
import os
from services.db import get_connection

def check_student_in_database():
    """Check if student 2025103006 exists in database and print details"""
    print("\n" + "="*60)
    print("CHECKING DATABASE FOR STUDENT 2025103006")
    print("="*60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check in students table
        cursor.execute('''
            SELECT student_id, student_number, last_name, first_name, email, 
                   face_data_path, created_at, updated_at 
            FROM students 
            WHERE student_number = '2025103006'
        ''')
        
        result = cursor.fetchone()
        
        if result:
            student_id, student_number, last_name, first_name, email, face_data_path, created_at, updated_at = result
            print(f"\n✓ Student found in database!")
            print(f"  Student ID: {student_id}")
            print(f"  Student Number: {student_number}")
            print(f"  Name: {first_name} {last_name}")
            print(f"  Email: {email}")
            print(f"  Face Data Path: {face_data_path if face_data_path else 'NULL ❌'}")
            print(f"  Created At: {created_at}")
            print(f"  Updated At: {updated_at}")
            
            return student_id, face_data_path
        else:
            print("\n✗ Student 2025103006 NOT found in database")
            return None, None
            
    except Exception as e:
        print(f"\n✗ Error querying database: {e}")
        return None, None
    finally:
        conn.close()

def check_face_data_directory():
    """Check if face data directory exists and contains files"""
    print("\n" + "="*60)
    print("CHECKING FACE DATA DIRECTORY")
    print("="*60)
    
    face_data_path = os.path.join("dataset", "2025103006")
    abs_path = os.path.abspath(face_data_path)
    
    print(f"\nChecking for directory: {face_data_path}")
    print(f"Absolute path: {abs_path}")
    
    if os.path.exists(face_data_path):
        print(f"✓ Directory exists!")
        
        files = os.listdir(face_data_path)
        print(f"  Files count: {len(files)}")
        
        if files:
            print(f"  Files:")
            total_size = 0
            for file in files:
                file_path = os.path.join(face_data_path, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                print(f"    - {file} ({file_size} bytes)")
            print(f"  Total size: {total_size} bytes")
        else:
            print(f"  ✗ Directory is empty - no face images!")
    else:
        print(f"✗ Directory does NOT exist!")

def check_enrollments(student_id):
    """Check if student has any enrollments"""
    if not student_id:
        return
    
    print("\n" + "="*60)
    print("CHECKING ENROLLMENTS")
    print("="*60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT e.enrollment_id, e.student_id, e.class_id, c.course_id, 
                   cr.course_code, c.section
            FROM enrollments e
            LEFT JOIN classes c ON e.class_id = c.class_id
            LEFT JOIN courses cr ON c.course_id = cr.course_id
            WHERE e.student_id = ?
        ''', (student_id,))
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n✓ Found {len(results)} enrollment(s):")
            for enrollment_id, student_id, class_id, course_id, course_code, section in results:
                print(f"  - Enrollment ID: {enrollment_id}, Class: {course_code} {section}")
        else:
            print(f"\n✗ No enrollments found for student")
            
    except Exception as e:
        print(f"\n✗ Error checking enrollments: {e}")
    finally:
        conn.close()

def main():
    """Main debug function"""
    print("\n\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  DEBUG: FACE DATA REGISTRATION FOR 2025103006".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # Check database
    student_id, face_data_path = check_student_in_database()
    
    # Check directory
    check_face_data_directory()
    
    # Check enrollments
    if student_id:
        check_enrollments(student_id)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if face_data_path is None:
        print("\n⚠️  ISSUE FOUND: face_data_path is NULL in database")
        print("   This is the root cause of the face recognition issue!")
        print("\n   ACTION: Use the updated registration API to re-register")
        print("   the student. The fix will now properly set face_data_path")
        print("   in the database after saving images.")
    elif face_data_path:
        print(f"\n✓ face_data_path is set to: {face_data_path}")
        if os.path.exists(face_data_path) and os.listdir(face_data_path):
            print("✓ Directory exists and contains files")
            print("✓ Registration appears to be working correctly")
        else:
            print("✗ But directory is empty or doesn't exist")
            print("   ACTION: Re-register the student to ensure images are saved")
    else:
        print("\n✗ Student not found in database")
        print("   ACTION: Register the student first")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
