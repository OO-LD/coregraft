# coregraft's own task runner. Instances get their Makefile from
# profiles/<name>/; this one lints and tests the template repository itself.

# --- init (template bootstrap; removed by `make init`) ---
.PHONY: init
init: ## Personalise this repository (first run after "Use this template")
	@uv run scripts/init.py
# --- end init ---

.PHONY: install
install: ## Install the virtual environment and the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running ty"
	@uv run ty check

.PHONY: test
test: ## Run the template integrity tests
	@echo "🚀 Testing the template: Running pytest"
	@uv run python -m pytest

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run zensical build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run zensical serve

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
