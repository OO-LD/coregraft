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
<!-- >>> benchmarks -->
| `make bench` | Runs the performance benchmarks |
<!-- <<< benchmarks -->

`make check` lints untracked files on purpose: `pre-commit run -a` skips them, which is how a new file passes locally and then fails in CI the moment it is committed.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main. Until a release App is configured, the release workflow skips itself instead of failing.

<!-- >>> benchmarks -->

## Benchmarks

`make bench` runs the performance benchmarks in `tests/benchmarks/`. On pull requests they also run in CI and upload their results.

To track them over time, create a project on [Bencher](https://bencher.dev) (free for public repositories), add a `BENCHER_API_TOKEN` secret and set `BENCHER_PROJECT` in `.github/workflows/main.yml`. Bencher then comments each pull request with a statistical comparison against the base branch. Without the secret the benchmarks still run; only the tracking step is skipped.

<!-- <<< benchmarks -->

## Updates from the template

This repository was generated from [coregraft](https://github.com/OO-LD/coregraft) and records which version in `.copier-answers.yml`. A weekly workflow checks whether the template has moved on and, if so, replays its changes here. Your own edits are preserved: copier re-applies them on top of the new template version rather than over it, and anything it cannot merge arrives as `<<<<<<<` conflict markers for a human to decide.

By default the update arrives as an **issue** naming the new version and the command to run:

```bash
uvx copier update --skip-answered --trust --conflict inline
```

To get it as a **pull request** instead, this repository needs a GitHub App, because GitHub refuses to let the built-in token create or update anything under `.github/workflows/`, and template updates routinely do. One-time setup:

1. Use or create a GitHub App with **Contents: read and write**, **Pull requests: read and write** and **Workflows: read and write**. The last one is the whole point; without it the push is rejected. Organisations often already have a release App, which may need the Workflows permission added and the updated permission accepted on each installation.
2. Install the App on this repository.
3. Provide `RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY` as repository secrets, or share the organisation secrets with this repository. Installing the App and sharing the secret are two separate settings.

The workflow detects the secret at runtime, so it opens a pull request once the App is available and falls back to an issue when it is not. Either way the merge is the same; only the automation differs.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
