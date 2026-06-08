.PHONY: run test demo lint clean install frontend

# ─── Run ────────────────────────────────────────────────
run:
	python main.py

run-demo:
	DEMO_MODE=true python main.py

# ─── Demo ───────────────────────────────────────────────
demo:
	python demo/simulate_incident.py

demo-metrics:
	python demo/generate_metrics.py

# ─── Test ───────────────────────────────────────────────
test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=html

# ─── Lint ───────────────────────────────────────────────
lint:
	python -m ruff check src/ tests/

lint-fix:
	python -m ruff check --fix src/ tests/

# ─── Install ───────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -e ".[dev]"

# ─── Frontend ──────────────────────────────────────────
frontend:
	cd frontend && npm install && npm run build

frontend-dev:
	cd frontend && npm install && npm run dev

# ─── Clean ─────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage build dist *.egg-info
	rm -rf frontend/dist frontend/build
