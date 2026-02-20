import sqlite3
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()
cursor.execute("SELECT email, password, role FROM users WHERE role = 'super_admin'")
users = cursor.fetchall()
print('Super admin users:', users)
conn.close()