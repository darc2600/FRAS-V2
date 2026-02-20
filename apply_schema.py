import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

with open('database/user_types_schema.sql', 'r') as f:
    cursor.executescript(f.read())

conn.commit()
print('User types schema applied')

conn.close()