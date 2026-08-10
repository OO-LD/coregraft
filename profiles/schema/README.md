# coregraft-example

A coregraft example project

## Development

```bash
make install    # Node dependencies + pre-commit hooks
make validate   # validate schemas and example instances
make spec       # render the specification from spec/sections/
make check      # validate, render, lint, and verify the spec is current
make docs       # serve the documentation
```

Schemas live in `schemas/` (`*.schema.json` with optional `*.instance.json` examples). Every release publishes them under `/<version>/schemas/`, so a `$ref` or `@context` can point at an immutable URL.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
