from pathlib import Path
import os
import sys

import psycopg2


ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "database" / "v2_schema.sql"


def load_local_env() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)

    print("FRAS V2 database schema initialized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
