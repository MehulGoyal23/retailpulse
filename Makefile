.PHONY: up down build logs clean load-data db-shell test generate help

# ── Colors ────────────────────────────────────────────────
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)RetailPulse — Docker + Tableau Analytics$(RESET)"
	@echo "────────────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

up: ## Start all Docker services (build if needed)
	@echo "$(CYAN)Starting RetailPulse services...$(RESET)"
	docker compose up --build -d
	@echo "$(GREEN)✓ Services running. API → http://localhost:5000$(RESET)"

down: ## Stop all Docker services
	@echo "$(CYAN)Stopping services...$(RESET)"
	docker compose down
	@echo "$(GREEN)✓ Services stopped$(RESET)"

build: ## Rebuild all Docker images
	docker compose build --no-cache

logs: ## Tail logs from all containers
	docker compose logs -f

logs-api: ## Tail API container logs only
	docker compose logs -f api

logs-etl: ## Tail ETL container logs only
	docker compose logs -f etl

load-data: ## Run ETL to load CSV data into PostgreSQL
	@echo "$(CYAN)Loading sales data into PostgreSQL...$(RESET)"
	docker compose run --rm etl python loader.py
	@echo "$(GREEN)✓ Data loaded successfully$(RESET)"

generate: ## Generate fresh synthetic sales CSV data
	@echo "$(CYAN)Generating synthetic sales data...$(RESET)"
	python scripts/generate_data.py
	@echo "$(GREEN)✓ CSV files written to ./data/$(RESET)"

db-shell: ## Open a psql shell inside the postgres container
	docker compose exec postgres psql -U $${POSTGRES_USER:-retailuser} -d $${POSTGRES_DB:-retailpulse}

test: ## Run API tests inside Docker
	@echo "$(CYAN)Running tests...$(RESET)"
	docker compose exec api python -m pytest tests/ -v

test-local: ## Run tests locally (requires local Python env)
	cd api && python -m pytest tests/ -v

health: ## Check health of all services
	@echo "$(CYAN)Checking service health...$(RESET)"
	@bash scripts/health_check.sh

clean: ## Remove all containers, networks, and volumes (⚠ data loss)
	@echo "$(CYAN)Cleaning up all Docker resources...$(RESET)"
	docker compose down -v --remove-orphans
	@echo "$(GREEN)✓ Cleaned$(RESET)"

admin: ## Start with PgAdmin UI on :8080
	docker compose --profile admin up -d

ps: ## Show running containers
	docker compose ps

restart: ## Restart all services
	docker compose restart
