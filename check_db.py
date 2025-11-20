import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Current Database Tables:')
for table in tables:
    print(f'  - {table[0]}')

# Check if user_type columns exist
tables_to_check = ['students', 'instructors', 'admins']
for table in tables_to_check:
    try:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        user_type_exists = any(col[1] == 'user_type' for col in columns)
        print(f'{table}: user_type column = {user_type_exists}')
        
        # Show sample data
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'{table}: {count} records')
    except Exception as e:
        print(f'{table}: Error - {e}')

# Check for permissions/roles tables
role_tables = ['users', 'permissions', 'role_permissions', 'system_settings', 'audit_logs']
print('\nRole/Permission Tables:')
for table in role_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f'{table}: EXISTS ({count} records)')
    except:
        print(f'{table}: NOT FOUND')

conn.close()