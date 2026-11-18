# coregraft-example

A coregraft example project

Reference schemas that build on the [OO-LD reference schemas](https://schemas.oo-ld.org/). The schemas live in
`modules/<name>/`, the identity in `reference-schemas.toml`.

## Development

One command mirrors CI. Run it before every push:

```bash
make ci
```

It runs these in order, and each is also usable on its own:

| Command | Does |
| --- | --- |
| `make check` | Checks the Markdown extensions and lints |
| `make test` | Runs the tests (nothing yet: the engine arrives with a later snapshot) |
| `make docs-test` | Builds the documentation strictly, failing on any warning |

Everything else, or `make help` for the full list:

| Command | Does |
| --- | --- |
| `make install` | Installs the environment and the git hooks |
| `make check-extensions` | Checks `zensical.toml` against Zensical's defaults |
| `make docs` | Serves the documentation locally |

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases, the changelog and versioned documentation are automated on merge to main. Until a release App is configured, the release workflow skips itself instead of failing.

## Updates from the template

This repository was generated from [coregraft](https://github.com/OO-LD/coregraft) and records which version in `.copier-answers.yml`. A weekly workflow checks whether the template has moved on and, if so, replays its changes here. Your own edits are preserved: copier re-applies them on top of the new template version rather than over it, and anything it cannot merge arrives as `<<<<<<<` conflict markers for a human to decide.

By default the update arrives as an **issue** naming the new version and the command to run:

```bash
uvx copier update --skip-answered --trust --conflict inline
```

To get it as a **pull request** instead, this repository needs a GitHub App with **Contents**, **Pull requests** and **Workflows** write access, installed on this repository, with `RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY` as repository secrets. The workflow detects the secret at runtime, so it opens a pull request once the App is available and falls back to an issue when it is not.

---

Generated from [coregraft](https://github.com/OO-LD/coregraft).
