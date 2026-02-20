import sqlite3

# Enable WAL mode to prevent database locking issues
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Enable WAL (Write-Ahead Logging) mode
cursor.execute('PRAGMA journal_mode=WAL')
result = cursor.fetchone()
print(f'Journal mode: {result[0]}')

# Set timeout to allow retries on lock
conn.execute('PRAGMA busy_timeout = 5000')  # 5 seconds

conn.commit()
conn.close()

print('✅ Database configured to use WAL mode and 5-second timeout')
print('This prevents "database is locked" errors')
