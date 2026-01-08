#!/usr/bin/env python3
"""
Quick check script to verify face_data_path for any student
Usage: python check_face_path.py <student_number>
Example: python check_face_path.py 2025103006
"""

import sys
import sqlite3
import os
from services.db import get_connection

def check_student_face_path(student_number):
    """Check face_data_path for a specific student"""
    
    print(f"\nChecking face data for student: {student_number}")
    print("-" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT student_id, student_number, first_name, last_name, 
                   face_data_path, created_at 
            FROM students 
            WHERE student_number = ?
        ''', (student_number,))
        
        result = cursor.fetchone()
        
        if result:
            student_id, num, fname, lname, face_path, created = result
            print(f"Student: {fname} {lname} ({num})")
            print(f"Student ID: {student_id}")
            print(f"Created: {created}")
            print()
            
            # Check face_data_path
            if face_path is None:
                print(f"❌ face_data_path: NULL (THIS IS THE PROBLEM)")
            else:
                print(f"✓ face_data_path: {face_path}")
                
                # Check if directory exists
                if os.path.exists(face_path):
                    files = os.listdir(face_path)
                    print(f"✓ Directory exists with {len(files)} file(s)")
                    if files:
                        for f in files[:5]:  # Show first 5 files
                            size = os.path.getsize(os.path.join(face_path, f))
                            print(f"  - {f} ({size} bytes)")
                        if len(files) > 5:
                            print(f"  ... and {len(files)-5} more files")
                else:
                    print(f"❌ Directory does NOT exist: {face_path}")
        else:
            print(f"❌ Student {student_number} not found in database")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        student_num = sys.argv[1]
    else:
        student_num = "2025103006"  # Default
    
    check_student_face_path(student_num)
