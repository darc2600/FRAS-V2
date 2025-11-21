import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Add support permissions
cursor.execute('INSERT OR IGNORE INTO permissions (permission_name, description, category) VALUES (?, ?, ?)', ('submit_support', 'Submit support tickets', 'support'))
cursor.execute('INSERT OR IGNORE INTO permissions (permission_name, description, category) VALUES (?, ?, ?)', ('manage_support', 'View and manage support tickets', 'support'))

# Get permission IDs
cursor.execute('SELECT permission_id FROM permissions WHERE permission_name = ?', ('submit_support',))
submit_id = cursor.fetchone()[0]

cursor.execute('SELECT permission_id FROM permissions WHERE permission_name = ?', ('manage_support',))
manage_id = cursor.fetchone()[0]

# Add role permissions
cursor.execute('INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)', ('regular', submit_id))
cursor.execute('INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)', ('it_admin', submit_id))
cursor.execute('INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)', ('it_admin', manage_id))
cursor.execute('INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)', ('super_admin', submit_id))
cursor.execute('INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES (?, ?)', ('super_admin', manage_id))

conn.commit()
print('Support permissions added successfully')

conn.close()