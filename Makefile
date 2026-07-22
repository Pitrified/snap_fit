# Variables
PYTHON := uv run python
APP := snap_fit.webapp.main:app

.PHONY: help install run dev lint clean nbstrip pipelines-check

# magic to show the commands with their help text when you run `make help`
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync --all-extras --all-groups

run: ## Run the production server
	uv run uvicorn $(APP) --host 0.0.0.0 --port 8000

dev: ## Run the development server with hot reload
	uv run uvicorn $(APP) --reload

lint: ## Run the same checks as pre-commit and the editor (ruff, format, pyright)
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright

clean: ## Remove python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

nbstrip: ## Strip outputs from all tracked notebooks (the nbstripout hook only verifies)
	@files="$$(git ls-files '*.ipynb')"; \
	if [ -n "$$files" ]; then uv run nbstripout $$files; else echo "no tracked notebooks"; fi

pipelines-check: ## Check pipeline entries still import against the current API
	$(PYTHON) scripts/check_pipeline_imports.py
