# The validator and the specification these schemas conform to are one release. Pinned so a
# local run and CI judge the same way.
OOLD_PY_VERSION ?= 2.0.0
OOLD := uvx --from "oold[validation]==$(OOLD_PY_VERSION)" oold
# The engine (engine/) is a snapshot owned by the template: run it, never edit it.
RUN := uv run python

.PHONY: install
install: ## Install the virtual environment and the git hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: lock
lock: ## Resolve and write the lock of every module
	@$(RUN) engine/lock.py

.PHONY: package
package: lock ## Build the offline package of every module (docs/packages/, not committed)
	@$(RUN) engine/package.py

.PHONY: validate
validate: package ## Validate the modules, their example instances and the package
	@for dir in modules/*/; do \
		ls $$dir*.schema.json >/dev/null 2>&1 || continue; \
		$(OOLD) validate $$dir || exit 1; \
		for instance in $$dir*.instance.json; do \
			test -e "$$instance" || continue; \
			$(OOLD) validate-instance $$instance || exit 1; \
		done; \
		uv run --with pyld python engine/effective_views.py $$dir || exit 1; \
	done
	@uv run --with jsonschema --with referencing python engine/check_package.py

.PHONY: request-inclusion
request-inclusion: ## Print the link that asks the OO-LD reference schemas to list this repository (after a release)
	@$(RUN) scripts/request_inclusion.py

.PHONY: bump
bump: ## Raise the schema versions the changes since the last release require
	@$(RUN) engine/level.py --apply

.PHONY: bump-check
bump-check: ## Fail if the commits since the last release imply a smaller version than the schemas need
	@$(RUN) engine/bump.py --check

.PHONY: check-identifiers
check-identifiers: ## After a release: check every identifier resolves (needs the published site)
	@$(RUN) engine/check_identifiers.py --require

.PHONY: check-extensions
check-extensions: ## Check zensical.toml still restates Zensical's default Markdown extensions
	@uv run python scripts/check_markdown_extensions.py

.PHONY: check
check: check-extensions ## Run all quality checks
	@echo "🚀 Linting: Running pre-commit"
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard)
	@echo "🚀 Checking locks, versions and the pinned specification edition"
	@$(RUN) engine/lock.py --check
	@$(RUN) engine/level.py --check
	@$(RUN) engine/spec_edition.py --check
	@$(RUN) engine/check_enums.py

.PHONY: test
test: validate ## Validate the schemas and their example instances

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
