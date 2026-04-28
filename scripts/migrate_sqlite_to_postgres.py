#!/usr/bin/env python3
"""
Upsert missing rows from SQLite into Postgres (safe, idempotent).

Usage examples:
  # Dry-run inside container (let container expand DATABASE_URL):
  docker exec -it fras-backend-1 /bin/bash -c 'python3 /app/scripts/migrate_sqlite_to_postgres.py --sqlite /app/data/attendance.db --pg "$DATABASE_URL" --dry-run'

  # Or run on host pointing to local sqlite and DATABASE_URL in env:
  python3 scripts/migrate_sqlite_to_postgres.py --sqlite data/attendance.db --pg "$DATABASE_URL" --dry-run

The script is idempotent and uses ON CONFLICT DO NOTHING for inserts.
"""
import argparse
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List

try:
    import psycopg2
    from psycopg2 import sql
except Exception:
    psycopg2 = None


def sqlite_table_info(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = []
    for cid, name, ctype, notnull, dflt_value, pk in cur.fetchall():
        cols.append({'cid': cid, 'name': name, 'type': ctype, 'notnull': bool(notnull), 'dflt_value': dflt_value, 'pk': int(pk)})
    return cols


def fetch_sqlite_pks(conn: sqlite3.Connection, table: str, pk_col: str) -> List[Any]:
    cur = conn.execute(f'SELECT "{pk_col}" FROM "{table}"')
    return [r[0] for r in cur.fetchall()]


def fetch_pg_pks(pg_conn, table: str, pk_col: str) -> List[Any]:
    cur = pg_conn.cursor()
    cur.execute(sql.SQL('SELECT {} FROM {}').format(sql.Identifier(pk_col), sql.Identifier(table)))
    return [r[0] for r in cur.fetchall()]


def fetch_sqlite_row(conn: sqlite3.Connection, table: str, cols: List[str], pk_col: str, pk_val: Any) -> Dict[str, Any]:
    cur = conn.execute(f'SELECT * FROM "{table}" WHERE "{pk_col}" = ? LIMIT 1', (pk_val,))
    row = cur.fetchone()
    if row is None:
        return {}
    return dict(zip(cols, row))


def insert_rows(pg_conn, table: str, cols: List[str], rows: List[Dict[str, Any]], pk_col: str, dry_run: bool = False) -> int:
    if not rows:
        return 0
    inserted = 0
    if dry_run:
        for r in rows:
            print('DRY:', table, '->', r)
        return 0

    cur = pg_conn.cursor()
    col_idents = [sql.Identifier(c) for c in cols]
    placeholders = sql.SQL(',').join(sql.Placeholder() * len(cols))
    insert_sql = sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING').format(
        sql.Identifier(table), sql.SQL(',').join(col_idents), placeholders, sql.Identifier(pk_col)
    )

    for r in rows:
        vals = [r.get(c) for c in cols]
        try:
            cur.execute(insert_sql, vals)
            inserted += 1
        except Exception as e:
            print('Insert error', table, 'pk=', r.get(pk_col), str(e))
            pg_conn.rollback()
            raise

    pg_conn.commit()
    return inserted


def sanitize_dsn(dsn: str) -> str:
    if not dsn:
        return dsn
    d = dsn.strip()
    if (d.startswith('"') and d.endswith('"')) or (d.startswith("'") and d.endswith("'")):
        d = d[1:-1]
    return d


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Upsert missing rows from SQLite into Postgres (safe, idempotent)')
    parser.add_argument('--sqlite', required=True, help='Path to SQLite file')
    parser.add_argument('--pg', required=False, help='Postgres DSN (e.g. postgres://user:pw@host:5432/db)')
    parser.add_argument('--tables', default='classes,enrollments,permissions,rooms', help='Comma-separated list of tables')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be inserted without performing inserts')
    parser.add_argument('--sample', type=int, default=5, help='Max sample rows to print per table')
    args = parser.parse_args(argv)

    if args.pg and psycopg2 is None:
        print('psycopg2 not installed in this Python environment. Install and re-run.', file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(args.sqlite):
        print('SQLite file not found:', args.sqlite, file=sys.stderr)
        sys.exit(2)

    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = None
    # Allow DSN to come from --pg or from the DATABASE_URL environment variable
    dsn = None
    if args.pg:
        dsn = args.pg
    else:
        dsn = os.environ.get('DATABASE_URL')
    dsn = sanitize_dsn(dsn) if dsn else None
    if dsn:
        try:
            pg_conn = psycopg2.connect(dsn)
        except Exception as e:
            print('Error connecting to Postgres with DSN:', repr(e), file=sys.stderr)
            sys.exit(2)
    else:
        # No DSN provided; only allow read-only dry-run behavior
        if not args.dry_run:
            print('No Postgres DSN provided via --pg or DATABASE_URL; provide one or run with --dry-run', file=sys.stderr)
            sys.exit(2)

    tables = [t.strip() for t in args.tables.split(',') if t.strip()]
    total_inserted = 0

    for t in tables:
        print(f"\nProcessing table {t}")
        try:
            info = sqlite_table_info(sqlite_conn, t)
        except Exception as e:
            print('  Skipping', t, '(not present in sqlite?)', e)
            continue

        cols = [c['name'] for c in info]
        pk_cols = [c['name'] for c in info if c['pk']]

        if len(pk_cols) != 1:
            print('  Skipping detailed PK diff for', t, '(composite or no PK)')
            continue
        pk = pk_cols[0]

        s_pks = set(fetch_sqlite_pks(sqlite_conn, t, pk))
        p_pks = set(fetch_pg_pks(pg_conn, t, pk)) if pg_conn else set()

        missing_in_pg = sorted(list(s_pks - p_pks))
        print(f"  sqlite rows: {len(s_pks)}, pg rows: {len(p_pks)}, missing in pg: {len(missing_in_pg)}")

        if not missing_in_pg:
            continue

        sample = missing_in_pg[: args.sample]
        print(f"  Preparing to insert {len(missing_in_pg)} rows into {t} (sample up to {args.sample}):")
        rows_to_insert = []
        for pkval in sample:
            row = fetch_sqlite_row(sqlite_conn, t, cols, pk, pkval)
            print('   -', json.dumps(row, default=str))
            rows_to_insert.append(row)

        if args.dry_run:
            for r in rows_to_insert:
                print('DRY:', t, '->', r)
            print(f"  Inserted: 0")
            continue

        inserted = insert_rows(pg_conn, t, cols, rows_to_insert, pk, dry_run=False)
        print(f"  Inserted: {inserted}")
        total_inserted += inserted

    print('\nTotal inserted:', total_inserted)


if __name__ == '__main__':
    main()
