import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('SELECT user_type, permission_name FROM role_permissions WHERE permission_name LIKE "%support%"')
results = cursor.fetchall()

print('Support permissions:')
for row in results:
    print(f'  {row[0]}: {row[1]}')

conn.close()