#!/usr/bin/env python3
"""
Compare SQLite and Postgres databases: table list, row counts, and missing PK rows.

Usage (inside container):
  python /app/scripts/compare_sqlite_postgres.py \
      --sqlite /app/data/attendance.db \
      --pg "$DATABASE_URL" \
      --sample 5

The script requires `psycopg2` to be installed in the environment used to run it.
"""
import argparse
import json
import sqlite3
import sys
from typing import Dict, List, Optional

try:
    import psycopg2
    from psycopg2 import sql
except Exception as e:
    psycopg2 = None


def list_sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [r[0] for r in cur.fetchall()]


def list_pg_tables(pg_conn) -> List[str]:
    cur = pg_conn.cursor()
    cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    rows = cur.fetchall()
    return [r[0] for r in rows]


def sqlite_table_info(conn: sqlite3.Connection, table: str) -> List[Dict]:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = []
    for cid, name, ctype, notnull, dflt_value, pk in cur.fetchall():
        cols.append({
            'cid': cid,
            'name': name,
            'type': ctype,
            'notnull': bool(notnull),
            'dflt_value': dflt_value,
            'pk': int(pk),
        })
    return cols


def pg_primary_key(pg_conn, table: str) -> List[str]:
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = 'public'
          AND tc.table_name = %s
        ORDER BY kcu.ordinal_position
    """, (table,))
    return [r[0] for r in cur.fetchall()]


def count_sqlite(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"")
    return cur.fetchone()[0]


def count_pg(pg_conn, table: str) -> int:
    cur = pg_conn.cursor()
    cur.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table)))
    return cur.fetchone()[0]


def fetch_sqlite_pks(conn: sqlite3.Connection, table: str, pk_col: str) -> List:
    cur = conn.execute(f"SELECT \"{pk_col}\" FROM \"{table}\"")
    return [r[0] for r in cur.fetchall()]


def fetch_pg_pks(pg_conn, table: str, pk_col: str) -> List:
    cur = pg_conn.cursor()
    cur.execute(sql.SQL('SELECT {} FROM {}').format(sql.Identifier(pk_col), sql.Identifier(table)))
    return [r[0] for r in cur.fetchall()]


def fetch_sqlite_row(conn: sqlite3.Connection, table: str, pk_col: str, pk_val):
    cur = conn.execute(f"SELECT * FROM \"{table}\" WHERE \"{pk_col}\" = ? LIMIT 1", (pk_val,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c['name'] for c in sqlite_table_info(conn, table)], row))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite', required=True, help='Path to sqlite file')
    parser.add_argument('--pg', required=False, help='Postgres DSN (e.g. postgres://user:pw@host:5432/db)')
    parser.add_argument('--sample', type=int, default=5, help='Sample missing rows to print per table')
    args = parser.parse_args()

    if args.pg and psycopg2 is None:
        print('psycopg2 not installed in this Python environment. Install it and re-run.', file=sys.stderr)
        sys.exit(2)

    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = None
    if args.pg:
        pg_conn = psycopg2.connect(args.pg)

    sqlite_tables = list_sqlite_tables(sqlite_conn)
    pg_tables = list_pg_tables(pg_conn) if pg_conn else []

    print('\nFound tables:')
    print('  sqlite:', len(sqlite_tables), 'tables')
    print('  postgres:', len(pg_tables), 'tables')

    common = sorted(set(sqlite_tables) & set(pg_tables))
    only_sqlite = sorted(set(sqlite_tables) - set(pg_tables))
    only_pg = sorted(set(pg_tables) - set(sqlite_tables))

    print('\nTables only in sqlite:')
    for t in only_sqlite:
        print('  -', t)

    print('\nTables only in postgres:')
    for t in only_pg:
        print('  -', t)

    print('\nComparing common tables:')
    report = {}
    for t in common:
        try:
            s_count = count_sqlite(sqlite_conn, t)
        except Exception as e:
            s_count = None
        try:
            p_count = count_pg(pg_conn, t)
        except Exception as e:
            p_count = None

        report[t] = {'sqlite_count': s_count, 'pg_count': p_count}
        print(f"\nTable {t}: sqlite={s_count} pg={p_count}")

        # attempt detailed PK-based diff for single-column integer PKs
        sqlite_info = sqlite_table_info(sqlite_conn, t)
        pk_cols = [c['name'] for c in sqlite_info if c['pk']]
        pg_pks = pg_primary_key(pg_conn, t)

        if len(pk_cols) == 1 and len(pg_pks) == 1 and pk_cols[0] == pg_pks[0]:
            pk = pk_cols[0]
            try:
                s_pks = set(fetch_sqlite_pks(sqlite_conn, t, pk))
                p_pks = set(fetch_pg_pks(pg_conn, t, pk))
            except Exception as e:
                print('  Could not fetch PK lists:', e)
                continue

            missing_in_pg = sorted(list(s_pks - p_pks))
            missing_in_sqlite = sorted(list(p_pks - s_pks))

            print(f"  PK column: {pk}  (sqlite PKs: {len(s_pks)}, pg PKs: {len(p_pks)})")
            print(f"  Missing in Postgres: {len(missing_in_pg)} rows")
            print(f"  Missing in Sqlite: {len(missing_in_sqlite)} rows")

            if missing_in_pg:
                report[t]['missing_in_pg_count'] = len(missing_in_pg)
                report[t]['missing_in_pg_sample'] = missing_in_pg[:args.sample]
                print(f"  Sample missing in PG (up to {args.sample}): {missing_in_pg[:args.sample]}")
                # print sample rows from sqlite
                for pkval in missing_in_pg[:args.sample]:
                    row = fetch_sqlite_row(sqlite_conn, t, pk, pkval)
                    print('   -', json.dumps(row, default=str))
            if missing_in_sqlite:
                report[t]['missing_in_sqlite_count'] = len(missing_in_sqlite)
                report[t]['missing_in_sqlite_sample'] = missing_in_sqlite[:args.sample]

        else:
            print('  Skipping detailed PK diff (composite or mismatched PKs)')

    # final JSON report
    print('\nSummary JSON:')
    print(json.dumps(report, indent=2, default=str))


if __name__ == '__main__':
    main()
