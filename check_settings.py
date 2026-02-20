#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM system_settings')
count = cursor.fetchone()[0]
print(f'Total system settings: {count}')

cursor.execute("SELECT setting_key, setting_value, setting_type FROM system_settings WHERE setting_key LIKE 'recognition%' OR setting_key LIKE 'image%' OR setting_key LIKE 'attendance%' OR setting_key LIKE 'min_face%' OR setting_key LIKE 'face_detection%'")
results = cursor.fetchall()
print('Recognition/Image/Attendance Settings:')
for row in results:
    print(f'  {row[0]}: {row[1]} ({row[2]})')

conn.close()