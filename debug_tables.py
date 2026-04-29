import sqlite3
from services.db import get_connection

with get_connection() as conn:
    cursor = conn.cursor()

# Check if support_tickets table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets'")
result = cursor.fetchone()
print('support_tickets table exists:', result is not None)

if result:
    cursor.execute('PRAGMA table_info(support_tickets)')
    columns = cursor.fetchall()
    print('Columns:')
    for col in columns:
        print(f'  {col[1]}: {col[2]}')

# Check if ticket_replies table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ticket_replies'")
result = cursor.fetchone()
print('ticket_replies table exists:', result is not None)

    # connection closed by context manager