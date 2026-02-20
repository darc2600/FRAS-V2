import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('SELECT rp.user_type, p.permission_name FROM role_permissions rp JOIN permissions p ON rp.permission_id = p.permission_id WHERE p.permission_name LIKE "%support%"')
results = cursor.fetchall()

print('Support permissions:')
for row in results:
    print(f'  {row[0]}: {row[1]}')

conn.close()