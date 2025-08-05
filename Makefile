# Basic Usage:
#   make <rule>             : Run a specific rule (e.g., make test)
#   make VAR=value <rule>   : Run rule with environment variable (e.g., make DOCS_PORT=8080 docs-serve)
#
# Common Rules: help, clean, test, format, lint, docs-serve
#
# Rules can depend on other rules which run first. Rules with _ prefix are internal helpers.

MODULE_NAME = soccerdata
PYTHON_VERSION = 3.9
PYTHON_INTERPRETER = python
DOCS_PORT ?= 8000
SOCCERDATA_DIR ?= tests/appdata
.DEFAULT_GOAL := help

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Utilities ━━━━━━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: all help

all: help

help: ## Show this help message
	@echo "\n\033[1m~ Available rules: ~\033[0m\n"
	@echo "For VSCode/Cursor, try: ⇧ ⌘ P, Tasks: Run Task\n"
	@grep -E '^[a-zA-Z][a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[38;5;222m%-30s\033[0m %s\n", $$1, $$2}'


# ━━━━━━━━━━━━━━━━━━━━━━━ Filesystem Cleaning ━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: clean _clean-mac _clean-python

clean: _clean-mac _clean-python ## Delete all compiled Python files and macOS-related files
	find . -type d -name ".cache" -delete

_clean-mac: ## Clean macOS-related files
	find . -type f -name "*.DS_store" -delete

_clean-python: ## Clean all compiled Python files
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Testing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: test test-fastest test-continuous test-debug-last _clean_manual_test

test: ## Run all tests
	SOCCERDATA_DIR=$(SOCCERDATA_DIR) MAX_AGE=604800 \
		       pytest \
			--cov=$(MODULE_NAME)

test-class: ## Run tests in a specific class
	SOCCERDATA_DIR=$(SOCCERDATA_DIR) MAX_AGE=604800 \
		pytest -k "$(filter-out $@,$(MAKECMDGOALS))" --cov=$(MODULE_NAME)

test-continuous: ## Run tests in watch mode using pytest-watcher
	SOCCERDATA_DIR=$(SOCCERDATA_DIR) MAX_AGE=604800 \
		ptw . --now --runner pytest --config-file pyproject.toml

test-debug-last: ## Debug last failed test with pdb
	SOCCERDATA_DIR=$(SOCCERDATA_DIR) MAX_AGE=604800 \
		pytest --lf --pdb

# ━━━━━━━━━━━━━━━━━━━━━━━━━ Quality Assurance ━━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: lint format mypy

lint: ## Lint using ruff (use `make format` to do formatting)
	ruff check --config pyproject.toml $(MODULE_NAME)

format: ## Format source code
	ruff format --config pyproject.toml $(MODULE_NAME)

mypy: ## Type check using mypy
	mypy --install-types --non-interactive --config-file pyproject.toml $(MODULE_NAME) tests

# ━━━━━━━━━━━━━━━━━━━━━━━━━━ Documentation ━━━━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: docs-serve docs-build

docs-serve: ## Serve documentation locally on port $(DOCS_PORT)
	sphinx-autobuild --host=0.0.0.0 --port=$(DOCS_PORT) docs docs/_build || \
	echo "\n\nInstance found running on $(DOCS_PORT), try killing process and rerun."

# Makes sure docs can be served prior to actually deploying
docs-build: ## Build and deploy documentation to GitHub Pages
	sphinx-build docs docs/_build

# ━━━━━━━━━━━━━━━━━━━━━ Packaging & Environment ━━━━━━━━━━━━━━━━━━━━ #

.PHONY: create-env
create-env: ## Set up python interpreter environment
	uv venv
	@echo ">>> New virtualenv with uv created. Activate with:\nsource '.venv/bin/activate'"

.PHONY: requirements
requirements: ## Install Python Dep
	uv sync

.PHONY: publish-all
publish-all: format lint publish docs-publish ## Run format, lint, publish package and docs

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━ Pre-Commits ━━━━━━━━━━━━━━━━━━━━━━━━━━ #

.PHONY: pre-commit-test pre-commit-update

pre-commit-test: ## Test hooks
	pre-commit run --all-files --show-diff-on-failure
	git add .pre-commit-config.yaml

pre-commit-update: ## Update, install, and test hooks w/ new config
	pre-commit autoupdate
	pre-commit install
	$(MAKE) pre-commit-test
