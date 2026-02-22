import sqlite3
import json
from datetime import datetime

DB_FILE = 'events_tracker.db'

def init_idealista_table():
    """Initialize Idealista table in database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idealista_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_idealista_data(data):
    """Save Idealista data to database"""
    init_idealista_table()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Delete old data
    cursor.execute('DELETE FROM idealista_data')
    
    # Insert new data
    cursor.execute('''
        INSERT INTO idealista_data (data, timestamp, last_updated)
        VALUES (?, ?, ?)
    ''', (
        json.dumps(data, ensure_ascii=False),
        data.get('timestamp', datetime.now().isoformat()),
        data.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ))
    
    conn.commit()
    conn.close()

def get_idealista_data():
    """Get Idealista data from database"""
    init_idealista_table()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT data FROM idealista_data ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return json.loads(row[0])
    else:
        return {'properties': [], 'timestamp': '', 'last_updated': 'Nunca'}
