"""
Database manager for tracking calendar events
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'events_tracker.db'

def init_database():
    """Initialize the events tracking database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            uid TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            date TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            copied_at TEXT,
            calendar_source TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def add_new_event(uid, summary, start_time, end_time, date, calendar_source="Casa Juana Doña"):
    """Add a new event to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO events (uid, summary, start_time, end_time, date, detected_at, status, calendar_source)
            VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
        """, (uid, summary, start_time, end_time, date, datetime.now().isoformat(), calendar_source))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Event already exists
        return False
    finally:
        conn.close()

def get_event_status(uid):
    """Get the status of an event"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM events WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

def mark_event_copied(uid):
    """Mark an event as copied"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE events 
        SET status = 'copied', copied_at = ?
        WHERE uid = ?
    """, (datetime.now().isoformat(), uid))
    
    conn.commit()
    conn.close()

def mark_event_ignored(uid):
    """Mark an event as ignored"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE events 
        SET status = 'ignored'
        WHERE uid = ?
    """, (uid,))
    
    conn.commit()
    conn.close()

def get_new_events():
    """Get all events with status 'new'"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT uid, summary, start_time, end_time, date, detected_at
        FROM events
        WHERE status = 'new'
        ORDER BY date ASC, start_time ASC
    """)
    
    events = []
    for row in cursor.fetchall():
        events.append({
            'uid': row[0],
            'summary': row[1],
            'start_time': row[2],
            'end_time': row[3],
            'date': row[4],
            'detected_at': row[5]
        })
    
    conn.close()
    return events

def get_all_known_uids():
    """Get all UIDs that are already in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT uid FROM events")
    uids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return set(uids)

# Auto-initialize database on import
init_database()

if __name__ == '__main__':
    print("Database ready!")
