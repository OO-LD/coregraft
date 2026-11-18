.PHONY: install
install: ## Install the virtual environment and the git hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check-extensions
check-extensions: ## Check zensical.toml still restates Zensical's default Markdown extensions
	@uv run python scripts/check_markdown_extensions.py

.PHONY: check
check: check-extensions ## Run all quality checks
	@echo "🚀 Linting: Running pre-commit"
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard)

.PHONY: test
test: ## Run the tests (the schema engine and its checks arrive with the engine snapshot)
	@echo "No engine snapshot yet: nothing to test."

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run zensical build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run zensical serve

.PHONY: ci
ci: check test docs-test ## Run everything CI runs, before pushing
	@# Name the branch: `make ci` is the last thing run before pushing, and a
	@# green gate on the wrong branch is an easy mistake to make.
	@branch=$$(git branch --show-current 2>/dev/null); \
		if [ -n "$$branch" ]; then \
			echo "✅ Ready to push on branch '$$branch'"; \
		else \
			echo "✅ Ready to push"; \
		fi

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
