# coregraft-example

A coregraft example project

Reference schemas that build on the [OO-LD reference schemas](https://schemas.oo-ld.org/). The schemas live in
`modules/<name>/`, the identity in `reference-schemas.toml`.

## The engine

`engine/` is a snapshot of the engine of the [OO-LD reference schemas](https://github.com/OO-LD/oold-reference-schemas), with `engine/ENGINE_MANIFEST.json` recording the tag and commit it came from. It belongs to the template: run it through `make`, never edit it. A template update replaces it as a whole. It needs Python 3.11 or newer.

## Development

One command mirrors CI. Run it before every push:

```bash
make ci
```

It runs these in order, and each is also usable on its own:

| Command | Does |
| --- | --- |
| `make check` | Lints, and checks the locks, versions, pinned specification edition and enums |
| `make test` | Validates the modules, their example instances and the package |
| `make docs-test` | Builds the documentation strictly, failing on any warning |

Everything else, or `make help` for the full list:

| Command | Does |
| --- | --- |
| `make install` | Installs the environment and the git hooks |
| `make lock` | Resolves and writes the lock of every module |
| `make package` | Builds the offline package of every module into `docs/packages/` (not committed) |
| `make request-inclusion` | After a release, prints a link that opens the inclusion form of the OO-LD reference schemas, filled in from this repository and the published package |
| `make bump` | Raises the schema versions the changes since the last release require |
| `make bump-check` | Fails if the commits imply a smaller version than the schemas need |
| `make check-identifiers` | After a release, checks every identifier resolves |
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
