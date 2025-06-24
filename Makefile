.PHONY: help setup install install-dev test test-unit test-integration test-full lint format type-check docker-build docker-up docker-down docker-logs load-data preprocess-csv preprocess-and-load clean migrate migrate-create check-all shell run reset-db debug-load-data ensure-db

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Complete project setup (build, start, install, migrate, load data)
	./scripts/setup.sh

test: ## Run all tests (with database setup)
	docker-compose exec app pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run ruff linter
	docker-compose exec app ruff check app/ tests/

format: ## Format code with ruff
	docker-compose exec app ruff format app/ tests/

type-check: ## Run basic type checking with ruff (checks imports and syntax)
	docker-compose exec app mypy app/

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

preprocess-csv: ## Preprocess CSV file for faster loading
	docker-compose exec app python scripts/preprocess_csv.py ./resources/2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv ./resources/preprocessed_mobile_sites.csv --convert-coordinates

preprocess-and-load: ## Preprocess CSV and load data
	docker-compose exec app python scripts/preprocess_and_load.py ./resources/2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv

load-preprocessed: ## Load preprocessed CSV data
	docker-compose exec app python scripts/load_data.py ./resources/preprocessed_mobile_sites.csv

debug-load-data: ## Load CSV data with debugger
	docker-compose exec app python -m pdb scripts/load_data.py

migrate: ## Run database migrations
	docker-compose exec app alembic upgrade head

run: ## Run the application locally (inside container)
	docker-compose exec app uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

reset-db: ## Reset database tables (drops and recreates)
	docker-compose exec app python scripts/reset_db.py 