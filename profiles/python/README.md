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
| `make check` | Lock file consistency, `pre-commit` on tracked and untracked files, `ty`, `deptry` |
| `make test` | `pytest` with coverage |
| `make docs-test` | Builds the documentation strictly, failing on any warning |

Everything else, or `make help` for the full list:

| Command | Does |
| --- | --- |
| `make install` | Creates the environment and installs the git hooks |
| `make docs` | Serves the documentation locally |
| `make build` | Builds a wheel into `dist/` |
| `make benchmark` | Runs the performance benchmarks |

`make check` lints untracked files on purpose: `pre-commit run -a` skips them, which is how a new file passes locally and then fails in CI the moment it is committed.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main. Until a release App is configured, the release workflow skips itself instead of failing.

## Benchmarks

`make benchmark` runs the performance benchmarks in `tests/benchmarks/`. On pull requests they also run in CI and upload their results.

To track them over time, create a project on [Bencher](https://bencher.dev) (free for public repositories), add a `BENCHER_API_TOKEN` secret and set `BENCHER_PROJECT` in `.github/workflows/main.yml`. Bencher then comments each pull request with a statistical comparison against the base branch. Without the secret the benchmarks still run; only the tracking step is skipped.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
