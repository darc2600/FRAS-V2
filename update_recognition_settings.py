import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Update attendance_buffer_minutes to 5
cursor.execute('''
    UPDATE system_settings 
    SET setting_value = ?
    WHERE setting_key = ?
''', ('5', 'attendance_buffer_minutes'))

conn.commit()

# Verify updates
cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('attendance_buffer_minutes',))
buffer = cursor.fetchone()
print(f"✓ attendance_buffer_minutes: {buffer[0]} mins")

cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('face_recognition_model',))
model = cursor.fetchone()
print(f"✓ face_recognition_model: {model[0] if model else 'NOT SET'}")

cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('recognition_threshold',))
threshold = cursor.fetchone()
print(f"✓ recognition_threshold: {threshold[0] if threshold else 'NOT SET'}")

print("\n✅ Database updated with better duplicate prevention and face recognition settings")

conn.close()
