VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
ALEMBIC = $(VENV)/bin/alembic
BLACK = $(VENV)/bin/black
ISORT = $(VENV)/bin/isort
PYLINT = $(VENV)/bin/pylint
PYTEST = $(VENV)/bin/pytest

dev:
	docker compose up --build

test:
	docker compose -f docker-compose.test.yml run --rm api pytest

migrate:
	$(ALEMBIC) upgrade head

seed:
	$(PYTHON) scripts/seed_superadmin.py
	$(PYTHON) scripts/seed_countries.py
	$(PYTHON) scripts/seed_languages.py
	$(PYTHON) scripts/sync_redis_counters.py

format:
	$(ISORT) app/ tests/ scripts/
	$(BLACK) app/ tests/ scripts/

lint:
	$(ISORT) --check app/ tests/ scripts/
	$(BLACK) --check app/ tests/ scripts/
	$(PYLINT) app/ --fail-under=8.0

typecheck:
	$(VENV)/bin/mypy app/
