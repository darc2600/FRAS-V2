import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('INSERT INTO support_tickets (user_id, subject, description, category, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
               (1, 'Test Ticket', 'Test Description', 'technical', 'medium', 'open'))

conn.commit()
print('Test ticket created')

cursor.execute('SELECT COUNT(*) FROM support_tickets')
count = cursor.fetchone()[0]
print(f'Total tickets: {count}')

conn.close()