#!/bin/bash
set -e

echo "Running migrations..."
docker compose exec api alembic upgrade head

echo "Seeding superadmin..."
docker compose exec -e PYTHONPATH=/app api python scripts/seed_superadmin.py

echo "Seeding countries..."
docker compose exec -e PYTHONPATH=/app api python scripts/seed_countries.py

echo "Seeding languages..."
docker compose exec -e PYTHONPATH=/app api python scripts/seed_languages.py

echo "Syncing Redis counters..."
docker compose exec -e PYTHONPATH=/app api python scripts/sync_redis_counters.py

echo "Done."
