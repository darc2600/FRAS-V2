import sqlite3
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE instructors ADD COLUMN user_type TEXT DEFAULT "regular"')
    print('Added user_type to instructors')
except Exception as e:
    print(f'user_type already exists in instructors or error: {e}')
try:
    cursor.execute('ALTER TABLE admins ADD COLUMN user_type TEXT DEFAULT "super_admin"')
    print('Added user_type to admins')
except Exception as e:
    print(f'user_type already exists in admins or error: {e}')
try:
    cursor.execute('ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT "regular"')
    print('Added user_type to users')
except Exception as e:
    print(f'user_type already exists in users or error: {e}')
conn.commit()
conn.close()