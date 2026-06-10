#!/usr/bin/env bash
set -euo pipefail

# FRAS V2 VPS redeploy helper
# Modes:
# - default: replace app containers/images but keep database volume
# - WIPE_DB=1: remove V2 database volume for a full clean reset

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.v2.yml}"
OLD_COMPOSE_FILE="${OLD_COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env}"
WIPE_DB="${WIPE_DB:-0}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"

echo "[INFO] Project directory: $PROJECT_DIR"
echo "[INFO] Compose file: $COMPOSE_FILE"
echo "[INFO] Old compose file: $OLD_COMPOSE_FILE"
echo "[INFO] Env file: $ENV_FILE"
echo "[INFO] WIPE_DB=$WIPE_DB"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[ERROR] Compose file not found: $COMPOSE_FILE"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Env file not found: $ENV_FILE"
  echo "[HINT] Create from .env.v2.example then update secrets."
  exit 1
fi

mkdir -p deployment/backups

if docker compose -f "$COMPOSE_FILE" ps db >/dev/null 2>&1; then
  echo "[INFO] Attempting database backup before redeploy..."
  ts="$(date +%Y%m%d_%H%M%S)"
  backup_path="deployment/backups/fras_v2_${ts}.sql"

  if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${POSTGRES_USER:-fras_v2}" "${POSTGRES_DB:-fras_v2}" > "$backup_path"; then
    echo "[INFO] Database backup saved to $backup_path"
  else
    echo "[WARN] Database backup skipped (db may not be running yet or credentials unavailable)."
    rm -f "$backup_path" || true
  fi
fi

echo "[INFO] Stopping and removing existing V2 containers..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans

if [[ -f "$OLD_COMPOSE_FILE" ]]; then
  echo "[INFO] Stopping and removing old production stack containers..."
  docker compose -f "$OLD_COMPOSE_FILE" down --remove-orphans || true
fi

if [[ "$WIPE_DB" == "1" ]]; then
  echo "[WARN] Full wipe mode enabled. Removing V2 volume(s)."
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
  if [[ -f "$OLD_COMPOSE_FILE" ]]; then
    docker compose -f "$OLD_COMPOSE_FILE" down -v --remove-orphans || true
  fi
  docker volume rm fras_fras_v2_postgres_data 2>/dev/null || true
  docker volume rm fras_v2_postgres_data 2>/dev/null || true
  docker volume rm fras_postgres_data 2>/dev/null || true
  docker volume rm postgres_data 2>/dev/null || true
fi

echo "[INFO] Pulling latest code changes (if repository is connected)..."
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch --all --prune || true
  current_branch="$(git rev-parse --abbrev-ref HEAD || echo main)"
  git pull --ff-only origin "$current_branch" || true
fi

echo "[INFO] Building and starting V2 stack..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "[INFO] Waiting for services..."
sleep 3

docker compose -f "$COMPOSE_FILE" ps

echo "[INFO] Health check: backend docs"
if curl -fsS http://127.0.0.1:${BACKEND_PORT:-8000}/docs >/dev/null; then
  echo "[INFO] Backend is reachable."
else
  echo "[WARN] Backend docs endpoint is not reachable yet. Check logs:"
  echo "       docker compose -f $COMPOSE_FILE logs --tail=100 backend"
fi

echo "[INFO] Done."
if [[ "$WIPE_DB" == "1" ]]; then
  echo "[NEXT] Initialize and seed from scratch:"
  echo "  docker compose -f $COMPOSE_FILE exec backend python database/init_v2_database.py --force"
  echo "  docker compose -f $COMPOSE_FILE exec backend python database/seed_v2_integration_data.py --docx /app/deployment/seed/FRAS-prof-database.docx --enroll-all-active-classes"
fi
