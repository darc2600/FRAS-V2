"""
DB compatibility wrapper.

Usage:
 from services.db import get_connection
 with get_connection() as conn:
     cursor = conn.cursor()
     cursor.execute('SELECT 1')

If DATABASE_URL env var is set the wrapper will connect to Postgres using psycopg2.
The wrapper adapts SQL parameter placeholders from '?' to '%s' for Postgres so existing
sqlite-style SQL in the repo continues to work.
"""
from __future__ import annotations

import os
import sqlite3
import logging
from typing import Optional
from datetime import datetime, date

LOG = logging.getLogger(__name__)

# Read DATABASE_URL at call-time to avoid import-time stale values when containers are recreated


class PGCursorWrapper:
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        adapted = sql.replace('?', '%s')
        return self._cur.execute(adapted, params or ())

    def executemany(self, sql, seq_of_params):
        adapted = sql.replace('?', '%s')
        return self._cur.executemany(adapted, seq_of_params)

    def fetchone(self):
        row = self._cur.fetchone()
        return self._convert_row(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        if rows is None:
            return rows
        return [self._convert_row(r) for r in rows]

    def _convert_row(self, row):
        if row is None:
            return None
        try:
            # row is typically a tuple
            return tuple(self._convert_value(v) for v in row)
        except Exception:
            return row

    def _convert_value(self, v):
        if isinstance(v, (datetime, date)):
            try:
                return v.isoformat()
            except Exception:
                return str(v)
        return v

    @property
    def description(self):
        return self._cur.description

    @property
    def rowcount(self):
        return getattr(self._cur, 'rowcount', -1)

    @property
    def lastrowid(self):
        return getattr(self._cur, 'lastrowid', None)


class PGConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PGCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # commit on exit if no exception (similar to sqlite3 context manager)
        if exc_type is None:
            try:
                self.commit()
            except Exception:
                LOG.exception('commit failed during __exit__')
        self.close()


def get_connection():
    """Return a connection-like object. Use Postgres if DATABASE_URL is set, otherwise sqlite."""
    # Read env var at call time so recreated containers pick up updated .env
    DATABASE_URL = os.environ.get('DATABASE_URL')
    # If DATABASE_URL explicitly points to a sqlite file use sqlite3
    if DATABASE_URL and DATABASE_URL.strip().lower().startswith('sqlite'):
        # Support urls like sqlite:///path/to/db or sqlite:///:memory:
        url = DATABASE_URL.strip()
        if url.startswith('sqlite:///'):
            path = url[len('sqlite:///'):]
        elif url.startswith('sqlite://'):
            path = url[len('sqlite://'):]
        else:
            path = url
        path = path or 'attendance.db'
        # in-memory special case or file-backed sqlite: create a real sqlite3.Connection
        if path in (':memory:', '/:memory:'):
            conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        else:
            # Use a reasonable timeout and allow cross-thread use in the app
            conn = sqlite3.connect(path or 'attendance.db', timeout=5.0, check_same_thread=False)
        # Enable WAL and a busy timeout for better concurrency
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout = 5000')
        conn.commit()
        return conn

    if DATABASE_URL:
        try:
            import psycopg2
        except Exception as e:
            LOG.exception('psycopg2 is required for Postgres but not installed: %s', e)
            raise
        # psycopg2 connection
        raw = psycopg2.connect(DATABASE_URL)
        return PGConnectionWrapper(raw)
    else:
        # default to sqlite file in project root with timeout and WAL mode
        path = 'attendance.db'
        conn = sqlite3.connect(path, timeout=5.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout = 5000')  # 5 seconds
        conn.commit()
        return conn
