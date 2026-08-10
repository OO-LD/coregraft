# Contributing

Contributions are welcome! You can help by reporting bugs, implementing features, or improving documentation. File issues and PRs at [github.com/OO-LD/coregraft](https://github.com/OO-LD/coregraft).

## Development setup

Requires `uv`, `make` and `git`.

```bash
git clone git@github.com:YOUR_NAME/coregraft.git && cd coregraft && make install
```

`make install` creates the environment and installs both the `pre-commit` and `commit-msg` stage hooks; the latter enforces Conventional Commits (see below).

## Making changes

1. Create a branch: `git checkout -b name-of-your-fix`
2. Make your changes; template behaviour is guarded by the tests in `tests/`
3. Run the checks: `make check`, `make test` and `make docs-test`
4. Commit and push, then open a pull request against `main`

| Target | Does |
| --- | --- |
| `make check` | lock consistency, pre-commit hooks, type check |
| `make test` | template integrity and macro tests |
| `make docs-test` | strict docs build, fails on any warning |
| `make docs` | serve the docs with live reload |

## Commit messages (Conventional Commits)

Commit messages drive versioning and the changelog automatically, so the format matters. The local `commit-msg` hook rejects malformed messages.

Format: `type(scope): subject`, for example `fix: correct broken profile prune`. The scope is optional.

| Type | Release effect | Use for |
| ---- | -------------- | ------- |
| `feat` | minor bump | a new feature |
| `fix`, `perf` | patch bump | a bug fix or performance improvement |
| `docs`, `chore`, `test`, `refactor`, `ci`, `style`, `build` | no release | changes that do not ship template behaviour |
| `BREAKING CHANGE:` footer, or `!` after the type | major bump | an incompatible change |

## Releasing

Releases are fully automated by python-semantic-release; see the [Releasing](README.md#releasing) section of the README. You never tag or bump versions by hand: the version lives in `pyproject.toml` and `TEMPLATE_VERSION`, both maintained by the release workflow.
