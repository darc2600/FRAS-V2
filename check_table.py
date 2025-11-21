import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="support_tickets"')
result = cursor.fetchone()
print('Table exists:', result is not None)

if result:
    cursor.execute('PRAGMA table_info(support_tickets)')
    cols = cursor.fetchall()
    print('Columns:')
    for col in cols:
        print(f'  {col[1]}: {col[2]}')

conn.close()