# Variables
PYTHON := uv run python
APP := snap_fit.webapp.main:app

.PHONY: help install run dev lint clean

# magic to show the commands with their help text when you run `make help`
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync --all-extras --all-groups

run: ## Run the production server
	uv run uvicorn $(APP) --host 0.0.0.0 --port 8000

dev: ## Run the development server with hot reload
	uv run uvicorn $(APP) --reload

lint: ## Run ruff for linting and formatting
	uv run ruff check .
	uv run ruff format --check .

clean: ## Remove python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
