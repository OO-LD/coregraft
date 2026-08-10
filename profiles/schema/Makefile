# Node runs the schema validator. Override when `node` is not on PATH
# (e.g. WSL with only a Windows install): make validate NODE="/c/.../node.exe"
NODE ?= node

.PHONY: install
install: ## Install the Node dependencies and the pre-commit hooks
	@echo "🚀 Installing Node dependencies"
	@npm install --silent
	@echo "🚀 Installing pre-commit hooks"
	@uv run pre-commit install

.PHONY: validate
validate: ## Validate the schemas and their example instances
	@echo "🚀 Validating schemas: Running ajv + JSON-LD checks"
	@"$(NODE)" scripts/validate.mjs

.PHONY: spec
spec: ## Render docs/spec/index.html from spec/sections/
	@echo "🚀 Rendering the specification"
	@uv run scripts/render_spec.py

.PHONY: stage-schemas
stage-schemas: ## Copy schemas/ into docs/ so every version serves them
	@mkdir -p docs/schemas
	@cp schemas/*.json docs/schemas/

.PHONY: check
check: validate spec stage-schemas ## Run all quality checks
	@echo "🚀 Linting: Running pre-commit"
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard)
	@echo "🚀 Checking the rendered spec is up to date"
	@git diff --exit-code docs/spec/index.html

.PHONY: test
test: validate ## Validate schemas (the test suite of a schema repository)

.PHONY: docs-test
docs-test: stage-schemas ## Test if documentation can be built without warnings or errors
	@uv run zensical build -s

.PHONY: docs
docs: stage-schemas ## Build and serve the documentation
	@uv run zensical serve

.PHONY: ci
ci: check test docs-test ## Run everything CI runs, before pushing
	@echo "✅ Ready to push"

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
