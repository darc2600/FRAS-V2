import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM support_tickets')
count = cursor.fetchone()[0]
print(f'Total tickets: {count}')

if count > 0:
    cursor.execute('SELECT ticket_id, user_id FROM support_tickets LIMIT 5')
    tickets = cursor.fetchall()
    print('Sample tickets:')
    for t in tickets:
        print(f'  ID: {t[0]}, User: {t[1]}')

    cursor.execute('SELECT COUNT(*) FROM users WHERE user_id IN (SELECT user_id FROM support_tickets)')
    valid_users = cursor.fetchone()[0]
    print(f'Valid users: {valid_users}')

conn.close()