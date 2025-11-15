import sqlite3

def add_instructor_number_column():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # Check if instructor_number column exists
    cursor.execute("PRAGMA table_info(instructors)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'instructor_number' not in columns:
        print('Adding instructor_number column to instructors table...')
        cursor.execute('ALTER TABLE instructors ADD COLUMN instructor_number VARCHAR(20)')
        # Create unique index for the column
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_instructor_number ON instructors(instructor_number)')
        print('Column and unique index added successfully!')
    else:
        print('instructor_number column already exists')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_instructor_number_column()