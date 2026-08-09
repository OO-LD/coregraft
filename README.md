# coregraft

🌿 Profiled GitHub template with full automation from commit to release, where the core keeps grafting forward into everything that grows from it.

## Use it

Press **Use this template**, then:

```bash
git clone https://github.com/<owner>/<repo>.git && cd <repo> && make init
```

`make init` asks for the profile, name, owner, license and optional extras, personalises the repository, removes what you did not ask for, and removes itself. No other tool to install.

## Profiles

| Profile | For | Brings |
| --- | --- | --- |
| `python` | Python packages | uv, hatchling, ruff, ty, pytest, PyPI publishing |
| `schema` | JSON Schema and JSON-LD | schema validation, specification rendering, published schema artifacts |

## Every repository gets

Self-documenting `Makefile`, `pre-commit` with ruff and conventional commits, `python-semantic-release` for versions and changelog, zensical docs with versioned publishing, scheduled link checking, and CI for quality, tests and releases.

Optional during `make init`: Dockerfile, dev container, benchmarks, `CITATION.cff`, coverage reporting.

## Staying in sync

Each generated repository records the template version it came from, so later template fixes can be replayed into it as a pull request.

## Status

Early. Skeleton in place, profiles in progress.

## License

Apache-2.0. Repositories created from this template pick their own license during `make init`.
