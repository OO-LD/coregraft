# coregraft

🌿 Profiled GitHub template with full automation from commit to release, where the core keeps grafting forward into everything that grows from it.

`coregraft` is a GitHub template repository. Press **Use this template**, run `make init`, and you get a repository that already has linting, typing, tests, docs, versioning and releases wired together. When the template improves later, those improvements can be grafted back into repositories that were created from it.

## Use it

Press **Use this template**, then:

```bash
git clone https://github.com/<owner>/<repo>.git && cd <repo> && make init
```

`make init` asks for the profile, name, owner, license and optional extras, personalises the repository, removes what you did not ask for, and removes itself. No other tool to install.

That is the whole workflow. There is no separate tool to install first.

## Profiles

| Profile | For | Brings |
| --- | --- | --- |
| `python` | Python packages | uv, hatchling, ruff, ty, pytest with coverage, PyPI publishing |
| `schema` | JSON Schema and JSON-LD projects | schema validation, specification rendering, published schema artifacts |

Profiles are overlays under `profiles/`. Adding another one later is additive and changes nothing that already exists.

## What every repository gets

| Area | Included |
| --- | --- |
| Tasks | A self-documenting `Makefile`, so `make help` lists everything |
| Quality | `pre-commit` with ruff, plus conventional commit messages enforced locally |
| Versioning | `python-semantic-release`, so versions and the changelog follow from commit messages |
| Docs | zensical, with versioned publishing and macros so documentation and example code share one source |
| Links | Link checking on a schedule, with an ignore list for the unavoidable exceptions |
| CI | A quality job, a test matrix and a release workflow |

Optional, chosen during `make init`: Dockerfile, dev container, benchmarks, `CITATION.cff` with Zenodo, code coverage reporting.

## Staying in sync

Every generated repository records which version of the template it came from. A maintenance workflow can later replay template changes into it as a pull request, so a fix made once here can reach every repository grown from it.

## Status

Early. The repository skeleton is in place and the profiles are being built. See the tracking issue for progress.

## License

Apache-2.0. Repositories created from this template choose their own license during `make init`.
