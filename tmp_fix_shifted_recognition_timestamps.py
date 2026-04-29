from services.db import get_connection

PREVIEW_SQL = """
SELECT log_id, student_id, class_id, timestamp, notes
FROM attendance_logs
WHERE notes LIKE ?
  AND timestamp >= ?
  AND (timestamp AT TIME ZONE 'UTC')::time = split_part(split_part(notes, 'Face recognized at ', 2), ' -', 1)::time
ORDER BY log_id;
"""

UPDATE_SQL = """
UPDATE attendance_logs
SET timestamp = timestamp - INTERVAL '8 hours'
WHERE notes LIKE ?
  AND timestamp >= ?
  AND (timestamp AT TIME ZONE 'UTC')::time = split_part(split_part(notes, 'Face recognized at ', 2), ' -', 1)::time;
"""

params = ("Face recognized at %", "2026-02-24 00:00:00+00")

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute(PREVIEW_SQL, params)
    rows = cur.fetchall()
    print("rows_to_fix=", len(rows))
    for row in rows:
        print(row)

    if rows:
        cur.execute(UPDATE_SQL, params)
        conn.commit()
        print("updated_rows=", len(rows))
    else:
        print("updated_rows=0")

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT log_id, student_id, class_id, timestamp, notes
        FROM attendance_logs
        WHERE log_id >= 344
        ORDER BY log_id DESC
        LIMIT 10
        """
    )
    print("recent_rows_after_fix=")
    for row in cur.fetchall():
        print(row)
