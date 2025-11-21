import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

query = '''SELECT t.ticket_id, t.user_id, t.subject, t.description, t.category, t.priority, t.status, t.assigned_to, t.created_at, t.updated_at, u.email as user_email, a.email as assigned_email FROM support_tickets t JOIN users u ON t.user_id = u.user_id LEFT JOIN users a ON t.assigned_to = a.user_id ORDER BY t.created_at DESC'''

try:
    cursor.execute(query)
    results = cursor.fetchall()
    print('Query executed successfully, results:', len(results))
    if results:
        print('First result:', results[0])
except Exception as e:
    print('Query failed:', str(e))

conn.close()