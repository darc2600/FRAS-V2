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

LOG = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')


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
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def description(self):
        return self._cur.description


class PGConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PGCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

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
        # default to sqlite file in project root
        return sqlite3.connect('attendance.db')
