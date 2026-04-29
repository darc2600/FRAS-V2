from services.db import get_connection

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT log_id, student_id, class_id, timestamp, notes
        FROM attendance_logs
        WHERE notes LIKE ?
        ORDER BY log_id DESC
        LIMIT 20
        """,
        ("Face recognized at %",),
    )
    rows = cur.fetchall()

print("rows:")
for row in rows:
    print(row)
