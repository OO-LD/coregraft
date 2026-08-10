# coregraft-example

A coregraft example project

## Development

```bash
make install   # environment + pre-commit hooks
make check     # lint, types, dependency audit
make test      # pytest with coverage
make docs      # serve the documentation
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main.

## Benchmarks

`make benchmark` runs the performance benchmarks in `tests/benchmarks/`. On pull requests they also run in CI and upload their results.

To track them over time, create a project on [Bencher](https://bencher.dev) (free for public repositories), add a `BENCHER_API_TOKEN` secret and set `BENCHER_PROJECT` in `.github/workflows/main.yml`. Bencher then comments each pull request with a statistical comparison against the base branch. Without the secret the benchmarks still run; only the tracking step is skipped.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
