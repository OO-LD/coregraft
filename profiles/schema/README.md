# coregraft-example

A coregraft example project

## Development

One command mirrors CI. Run it before every push:

```bash
make ci
```

It runs these in order, and each is also usable on its own:

| Command | Does |
| --- | --- |
| `make check` | Validates, renders the spec, stages the schemas, lints, and verifies the rendered spec is current |
| `make test` | Validates the schemas and their example instances |
| `make docs-test` | Builds the documentation strictly, failing on any warning |

Everything else, or `make help` for the full list:

| Command | Does |
| --- | --- |
| `make install` | Installs the Node dependencies and the git hooks |
| `make validate` | ajv and JSON-LD validation on their own |
| `make spec` | Renders `docs/spec/index.html` from `spec/sections/` |
| `make stage-schemas` | Copies `schemas/*.json` into the site |
| `make docs` | Serves the documentation locally |

Needs `node` on `PATH`. Override it per call when it is elsewhere: `make validate NODE=/path/to/node`.

Schemas live in `schemas/` (`*.schema.json` with optional `*.instance.json` examples). Every release publishes them under `/<version>/schemas/`, so a `$ref` or `@context` can point at an immutable URL.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main. Until a release App is configured, the release workflow skips itself instead of failing.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
