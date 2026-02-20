import sqlite3
import time

# Try to recover the database
db_path = 'attendance.db'

try:
    # Open with long timeout
    conn = sqlite3.connect(db_path, timeout=60.0)
    conn.execute('PRAGMA journal_mode=DELETE')  # Reset to delete mode first
    conn.commit()
    conn.close()
    print('✅ Database recovered and journal mode reset')
except Exception as e:
    print(f'Error: {e}')
    print('Trying alternative recovery...')
    try:
        # Give it more time
        time.sleep(5)
        conn = sqlite3.connect(db_path, timeout=120.0)
        conn.execute('PRAGMA quick_check')
        conn.close()
        print('✅ Database integrity verified')
    except Exception as e2:
        print(f'Still locked: {e2}')
