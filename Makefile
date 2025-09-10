PY = python3

.PHONY: run-backend lint test precommit install

run-backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --ssl-keyfile ssl/server.key --ssl-certfile ssl/server.crt

lint:
	ruff check --fix || true
	isort backend tests || true
	black backend tests || true

test:
	pytest -q

precommit:
	pre-commit install

install:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install pre-commit ruff black isort pytest
