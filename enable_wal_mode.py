import sqlite3
from services.db import get_connection

# Enable WAL mode to prevent database locking issues
with get_connection() as conn:
	cursor = conn.cursor()

	# Attempt to enable WAL (only meaningful for sqlite)
	try:
		cursor.execute('PRAGMA journal_mode=WAL')
		result = cursor.fetchone()
		if result:
			print(f'Journal mode: {result[0]}')
	except Exception:
		# Non-sqlite backends may ignore PRAGMA
		pass

	# Set timeout to allow retries on lock (sqlite-only)
	try:
		conn.execute('PRAGMA busy_timeout = 5000')  # 5 seconds
	except Exception:
		pass

print('✅ Database (if sqlite) configured to use WAL mode and 5-second timeout')
print('This helps prevent "database is locked" errors on sqlite')
