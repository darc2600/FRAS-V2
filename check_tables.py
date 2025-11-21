#!/usr/bin/env python3
"""
Check support ticket tables
"""

import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%ticket%'")
tables = cursor.fetchall()
print('Ticket tables:', [t[0] for t in tables])

conn.close()