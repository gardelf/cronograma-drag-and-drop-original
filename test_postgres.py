import os
from idealista_postgres import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM idealista_data')
    count = cursor.fetchone()[0]
    print(f"Total registros: {count}")
    
    cursor.execute('SELECT id, timestamp, last_updated FROM idealista_data ORDER BY id DESC LIMIT 5')
    rows = cursor.fetchall()
    print("\nÚltimos 5 registros:")
    for row in rows:
        print(f"  ID: {row[0]}, Timestamp: {row[1]}, Last Updated: {row[2]}")
    
    cursor.close()
    conn.close()
else:
    print("No se pudo conectar a PostgreSQL")
