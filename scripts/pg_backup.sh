#!/bin/bash
set -e
# Run from repo root
cd "$(dirname "$0")"/..

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

TIMESTAMP=$(date +%F-%H%M)
BACKUP_DIR=backups
mkdir -p "$BACKUP_DIR"

if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "POSTGRES_PASSWORD not set" >&2
  exit 1
fi

export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump -h 127.0.0.1 -U "${POSTGRES_USER:-postgres}" -F c -b -v -f "$BACKUP_DIR/frasdb-$TIMESTAMP.dump" "${POSTGRES_DB:-frasdb}"

# rotate old backups (>7 days)
find "$BACKUP_DIR" -name 'frasdb-*.dump' -type f -mtime +7 -delete

# optional upload to s3 if aws cli present and bucket configured
if command -v aws >/dev/null 2>&1 && [ -n "$AWS_S3_BUCKET" ]; then
  aws s3 cp "$BACKUP_DIR/frasdb-$TIMESTAMP.dump" "s3://$AWS_S3_BUCKET/frasdb-$TIMESTAMP.dump"
fi
