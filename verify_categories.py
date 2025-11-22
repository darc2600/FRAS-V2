#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check attendance settings
attendance_keys = ['absent_threshold_minutes', 'late_threshold_minutes', 'attendance_grace_period_minutes', 'auto_absent_delay_hours', 'duplicate_prevention_window_minutes', 'allow_makeup_attendance', 'makeup_deadline_hours']
cursor.execute(f"SELECT setting_key FROM system_settings WHERE setting_key IN ({','.join(['?']*len(attendance_keys))})", attendance_keys)
attendance = [row[0] for row in cursor.fetchall()]
print(f'Attendance settings found: {len(attendance)}/7')
print(f'Attendance: {attendance}')

# Check recognition settings
recognition_keys = ['recognition_threshold', 'min_face_confidence', 'face_detection_model', 'max_recognition_attempts', 'image_compression_quality', 'image_max_size']
cursor.execute(f"SELECT setting_key FROM system_settings WHERE setting_key IN ({','.join(['?']*len(recognition_keys))})", recognition_keys)
recognition = [row[0] for row in cursor.fetchall()]
print(f'Recognition settings found: {len(recognition)}/6')
print(f'Recognition: {recognition}')

# Check automation settings
automation_keys = ['auto_absent_enabled']
cursor.execute(f"SELECT setting_key FROM system_settings WHERE setting_key IN ({','.join(['?']*len(automation_keys))})", automation_keys)
automation = [row[0] for row in cursor.fetchall()]
print(f'Automation settings found: {len(automation)}/1')
print(f'Automation: {automation}')

# Check system settings
system_keys = ['system_name', 'theme_primary_color', 'theme_secondary_color', 'system_logo_url', 'welcome_message', 'user_guide']
cursor.execute(f"SELECT setting_key FROM system_settings WHERE setting_key IN ({','.join(['?']*len(system_keys))})", system_keys)
system = [row[0] for row in cursor.fetchall()]
print(f'System settings found: {len(system)}/6')
print(f'System: {system}')

conn.close()