import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cdi_stats.db')
USERS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.csv')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heure TEXT NOT NULL,
            sixieme INTEGER,
            cinquieme INTEGER,
            quatrieme INTEGER,
            troisieme INTEGER,
            total INTEGER,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_attendance(heure, sixieme, cinquieme, quatrieme, troisieme, total, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO attendance (heure, sixieme, cinquieme, quatrieme, troisieme, total, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (heure, sixieme, cinquieme, quatrieme, troisieme, total, date))
    conn.commit()
    conn.close()

def get_all_attendance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM attendance')
    rows = c.fetchall()
    conn.close()
    return rows

def authenticate(username, password):
    if not os.path.exists(USERS_CSV):
        return False
    with open(USERS_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                return True
    return False

# ...other database functions as needed...
