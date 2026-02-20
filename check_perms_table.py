import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('SELECT permission_name FROM permissions WHERE permission_name LIKE "%support%"')
results = cursor.fetchall()

print('Support permissions in permissions table:')
for row in results:
    print(f'  {row[0]}')

conn.close()