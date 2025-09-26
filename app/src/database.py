import sqlite3
import csv
import os
import datetime
import configparser
from datetime import datetime

def get_db_path():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.cfg')
    config.read(config_path, encoding='utf-8')
    base_name = config.get('Database', 'Base', fallback='cdi_stats.db')
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    db_path = os.path.join(data_dir, base_name)
    # Crée le fichier s'il n'existe pas
    if not os.path.exists(db_path):
        # On crée le fichier avec un nom normal : Base-[Année].db
        annee = datetime.now().year
        base_name = f"Base-{annee}.db"
        db_path = os.path.join(data_dir, base_name)
        open(db_path, 'a').close()
    return db_path

def get_users_csv():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, 'users.csv')

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
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
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO attendance (heure, sixieme, cinquieme, quatrieme, troisieme, total, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (heure, sixieme, cinquieme, quatrieme, troisieme, total, date))
    conn.commit()
    conn.close()

def get_all_attendance():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM attendance')
    rows = c.fetchall()
    conn.close()
    return rows

def authenticate(username, password):
    users_csv = get_users_csv()
    if not os.path.exists(users_csv):
        return False
    with open(users_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                return True
    return False

# ...autres fonctions de base de données si besoin...
