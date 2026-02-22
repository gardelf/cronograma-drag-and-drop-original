"""
Completed Tasks Database
Manages local storage of completed tasks to maintain cronograma structure
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# Use a path that works in both local and Railway environments
if os.path.exists('/app'):
    DB_PATH = os.getenv('DB_PATH', '/app/data/completed_tasks.db')
else:
    DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'data', 'completed_tasks.db'))

def init_db():
    """Initialize the completed tasks database"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            content TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            priority TEXT,
            labels TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date TEXT NOT NULL
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date 
        ON completed_tasks(date)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_task_id_date 
        ON completed_tasks(task_id, date)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Completed tasks database initialized")


def save_completed_task(
    task_id: str,
    content: str,
    start_time: str,
    end_time: str,
    priority: str = "P4",
    labels: List[str] = None,
    date: Optional[str] = None
):
    """
    Save a completed task to the database
    
    Args:
        task_id: Todoist task ID
        content: Task content/title
        start_time: Start time (HH:MM format)
        end_time: End time (HH:MM format)
        priority: Task priority (P1-P4)
        labels: List of task labels
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    labels_str = ",".join(labels) if labels else ""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if already exists (avoid duplicates)
    cursor.execute('''
        SELECT id FROM completed_tasks 
        WHERE task_id = ? AND date = ?
    ''', (task_id, date))
    
    if cursor.fetchone():
        print(f"   ⚠️  Task {task_id} already marked as completed for {date}")
        conn.close()
        return
    
    cursor.execute('''
        INSERT INTO completed_tasks 
        (task_id, content, start_time, end_time, priority, labels, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, content, start_time, end_time, priority, labels_str, date))
    
    conn.commit()
    conn.close()
    print(f"   ✅ Saved completed task: {content} ({start_time}-{end_time})")


def get_completed_tasks_for_date(date: Optional[str] = None) -> List[Dict]:
    """
    Get all completed tasks for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        List of completed task dictionaries
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_id, content, start_time, end_time, priority, labels, completed_at
        FROM completed_tasks
        WHERE date = ?
        ORDER BY start_time
    ''', (date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    completed_tasks = []
    for row in rows:
        task_id, content, start_time, end_time, priority, labels_str, completed_at = row
        completed_tasks.append({
            'id': task_id,
            'content': content,
            'start_time': start_time,
            'end_time': end_time,
            'priority': priority or 'P4',
            'labels': labels_str.split(',') if labels_str else [],
            'completed_at': completed_at,
            'completed': True
        })
    
    return completed_tasks


def cleanup_old_tasks(days_to_keep: int = 7):
    """
    Remove completed tasks older than specified days
    
    Args:
        days_to_keep: Number of days to keep (default 7)
    """
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM completed_tasks
        WHERE date < ?
    ''', (cutoff_date,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        print(f"   🗑️  Cleaned up {deleted_count} old completed tasks (older than {cutoff_date})")


# Initialize database on import
init_db()
