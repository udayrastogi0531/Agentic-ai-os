# ============================================
# Uday AI — Makefile
# ============================================

.PHONY: help dev backend frontend docker-up docker-down migrate test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ───────────────────────────────────

dev: ## Start all services for development
	docker compose -f docker/docker-compose.dev.yml up -d

backend: ## Start backend only (requires local Python env)
	cd backend && uvicorn app.main:app --reload --port 8000

frontend: ## Start frontend only
	cd frontend && npm run dev

# ── Docker ────────────────────────────────────────

docker-up: ## Start Docker services
	docker compose -f docker/docker-compose.dev.yml up -d

docker-down: ## Stop Docker services
	docker compose -f docker/docker-compose.dev.yml down

docker-build: ## Build Docker images
	docker compose -f docker/docker-compose.dev.yml build

docker-logs: ## View Docker logs
	docker compose -f docker/docker-compose.dev.yml logs -f

# ── Database ──────────────────────────────────────

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

# ── LLM ───────────────────────────────────────────

ollama-pull: ## Pull default Ollama model
	ollama pull qwen2.5:3b && ollama pull nomic-embed-text

# ── Testing ───────────────────────────────────────

test: ## Run all tests
	cd backend && pytest tests/ -v
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && pytest tests/ -v

# ── Cleanup ───────────────────────────────────────

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/data backend/logs
