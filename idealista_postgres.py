import os
import json
from datetime import datetime
import pytz

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        import psycopg2
        
        # Railway provides DATABASE_URL environment variable
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("⚠️ DATABASE_URL not found, falling back to empty data")
            return None
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"⚠️ Error connecting to PostgreSQL: {e}")
        return None

def init_idealista_table():
    """Initialize Idealista table in PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS idealista_data (
                id SERIAL PRIMARY KEY,
                data JSONB NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Idealista table initialized in PostgreSQL")
    except Exception as e:
        print(f"⚠️ Error initializing table: {e}")
        if conn:
            conn.close()

def save_idealista_data(data):
    """Save Idealista data to PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Cannot save Idealista data: no database connection")
        return
    
    try:
        init_idealista_table()
        
        cursor = conn.cursor()
        
        # Keep history, don't delete old data
        # Insert new data
        cursor.execute('''
            INSERT INTO idealista_data (data, timestamp, last_updated)
            VALUES (%s, %s, %s)
        ''', (
            json.dumps(data, ensure_ascii=False),
            datetime.now(),
            data.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Idealista data saved to PostgreSQL")
    except Exception as e:
        print(f"⚠️ Error saving Idealista data: {e}")
        if conn:
            conn.close()

def get_idealista_data():
    """Get latest Idealista data from PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Cannot load Idealista data: no database connection")
        return {'properties': [], 'timestamp': '', 'last_updated': 'Nunca'}
    
    try:
        init_idealista_table()
        
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM idealista_data ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            # PostgreSQL JSONB returns dict directly, no need to parse
            data = row[0]
            if isinstance(data, str):
                return json.loads(data)
            else:
                return data
        else:
            return {'properties': [], 'timestamp': '', 'last_updated': 'Nunca'}
    except Exception as e:
        print(f"⚠️ Error loading Idealista data: {e}")
        if conn:
            conn.close()
        return {'properties': [], 'timestamp': '', 'last_updated': 'Nunca'}

def get_idealista_comparison():
    """Get current and previous Idealista data for comparison"""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Cannot load Idealista data: no database connection")
        return None, None
    
    try:
        init_idealista_table()
        
        cursor = conn.cursor()
        
        # Get latest 2 records
        cursor.execute('SELECT data, timestamp FROM idealista_data ORDER BY id DESC LIMIT 2')
        rows = cursor.fetchall()
        
        print(f"🔍 DEBUG get_idealista_comparison: Found {len(rows)} records")
        
        cursor.close()
        conn.close()
        
        if len(rows) >= 2:
            # Current data (most recent)
            # Convert to Madrid timezone
            madrid_tz = pytz.timezone('Europe/Madrid')
            
            current_data = rows[0][0]
            current_timestamp = rows[0][1]
            if isinstance(current_data, str):
                current_data = json.loads(current_data)
            # Convert UTC to Madrid time
            if current_timestamp.tzinfo is None:
                current_timestamp = pytz.utc.localize(current_timestamp)
            current_timestamp_madrid = current_timestamp.astimezone(madrid_tz)
            current_data['timestamp'] = current_timestamp_madrid.strftime('%Y-%m-%d %H:%M:%S')
            
            # Previous data (second most recent)
            previous_data = rows[1][0]
            previous_timestamp = rows[1][1]
            if isinstance(previous_data, str):
                previous_data = json.loads(previous_data)
            # Convert UTC to Madrid time
            if previous_timestamp.tzinfo is None:
                previous_timestamp = pytz.utc.localize(previous_timestamp)
            previous_timestamp_madrid = previous_timestamp.astimezone(madrid_tz)
            previous_data['timestamp'] = previous_timestamp_madrid.strftime('%Y-%m-%d %H:%M:%S')
            
            return current_data, previous_data
        elif len(rows) == 1:
            # Only one record, no comparison possible
            madrid_tz = pytz.timezone('Europe/Madrid')
            
            current_data = rows[0][0]
            current_timestamp = rows[0][1]
            if isinstance(current_data, str):
                current_data = json.loads(current_data)
            # Convert UTC to Madrid time
            if current_timestamp.tzinfo is None:
                current_timestamp = pytz.utc.localize(current_timestamp)
            current_timestamp_madrid = current_timestamp.astimezone(madrid_tz)
            current_data['timestamp'] = current_timestamp_madrid.strftime('%Y-%m-%d %H:%M:%S')
            return current_data, None
        else:
            return None, None
    except Exception as e:
        print(f"⚠️ Error loading Idealista comparison: {e}")
        if conn:
            conn.close()
        return None, None
