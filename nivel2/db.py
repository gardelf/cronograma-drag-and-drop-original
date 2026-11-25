import os
from contextlib import contextmanager
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

@contextmanager
def connect():
    url = os.environ.get('NIVEL2_DATABASE_URL')
    if not url:
        raise RuntimeError('NIVEL2_DATABASE_URL required; no fallback to other databases')
    conn = psycopg2.connect(url, connect_timeout=8, cursor_factory=RealDictCursor)
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def migrate():
    from .seed import seed
    with connect() as conn, conn.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(26251101)')
        cur.execute('CREATE TABLE IF NOT EXISTS n2_schema_versions(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())')
        for path in sorted((Path(__file__).parent / 'migrations').glob('*.sql')):
            version = int(path.name.split('_')[0])
            cur.execute('SELECT version FROM n2_schema_versions WHERE version=%s', (version,))
            if not cur.fetchone():
                cur.execute(path.read_text())
                cur.execute('INSERT INTO n2_schema_versions(version) VALUES (%s)', (version,))
        seed(cur)
