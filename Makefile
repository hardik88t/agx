.PHONY: help install editable build sync sync-restart doctor lint format test clean clear completion-bash completion-zsh

UV := $(shell which uv 2>/dev/null || echo "uv")
REPO_DIR := $(shell pwd)

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Reinstall agx globally in uv tool environment
	$(UV) tool install --reinstall .

editable: ## Install agx in editable development mode (live updates)
	$(UV) tool install --editable . --force

build: ## Compile standalone single-file binary to dist/agx
	$(UV) run --with pyinstaller pyinstaller --onefile --name agx --add-data "src/agx/config.example.toml:agx" src/agx/main.py

doctor: ## Run diagnostic health check
	$(UV) run agx doctor

sync: ## Run bidirectional index synchronization
	$(UV) run agx sync

sync-restart: ## Stop IDE, sync state, and relaunch IDE
	$(UV) run agx sync -r

lint: ## Run code linter
	$(UV) run ruff check .

format: ## Run code formatter
	$(UV) run ruff format .

test: ## Run test suite
	$(UV) run pytest

completion-bash: ## Install shell autocompletion for Bash
	$(UV) run agx --install-completion bash

completion-zsh: ## Install shell autocompletion for Zsh
	$(UV) run agx --install-completion zsh

clean: ## Clean build artifacts and caches
	rm -rf dist build *.egg-info .pytest_cache *.spec .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

clear: clean ## Alias for clean
