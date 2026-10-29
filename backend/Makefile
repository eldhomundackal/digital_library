EXEC = docker compose exec api

dev:
	docker compose up --build

test:
	docker compose -f docker-compose.test.yml run --rm api pytest

migrate:
	$(EXEC) alembic upgrade head

seed:
	$(EXEC) -e PYTHONPATH=/app python scripts/seed_superadmin.py
	$(EXEC) -e PYTHONPATH=/app python scripts/seed_countries.py
	$(EXEC) -e PYTHONPATH=/app python scripts/seed_languages.py
	$(EXEC) -e PYTHONPATH=/app python scripts/sync_redis_counters.py

seed-test:
	$(EXEC) python scripts/seed_test_data.py

format:
	$(EXEC) isort app/ tests/ scripts/
	$(EXEC) black app/ tests/ scripts/

lint:
	$(EXEC) isort --check app/ tests/ scripts/
	$(EXEC) black --check app/ tests/ scripts/
	$(EXEC) pylint app/ --fail-under=8.0

typecheck:
	$(EXEC) mypy app/
