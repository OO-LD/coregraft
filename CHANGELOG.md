# CHANGELOG

All notable changes to this project are documented here. Versions are cut
automatically from Conventional Commits on every merge to main by
[python-semantic-release](https://python-semantic-release.readthedocs.io/). Do
not edit released sections by hand.

<!-- version list -->

## v0.10.0 (2026-08-11)


## v0.9.1 (2026-08-11)

### Bug Fixes

- **template**: Make the profile assembler safe to re-run on update
  ([`0da5f96`](https://github.com/OO-LD/coregraft/commit/0da5f9643ff57455288011f92f3fc54d8058d7a1))


## v0.9.0 (2026-08-11)

### Features

- **template**: Fix first-run defects and guide the questionnaire
  ([`72668b9`](https://github.com/OO-LD/coregraft/commit/72668b91f5161b559eeaffc433592baee433bc9c))


## v0.8.2 (2026-08-11)

### Bug Fixes

- **template**: Gate the dockerfile question to the python profile
  ([`5f93fb8`](https://github.com/OO-LD/coregraft/commit/5f93fb82d62440e533c51b5ce92b17fbeef3b015))


## v0.8.1 (2026-08-10)

### Bug Fixes

- **ci**: Exclude dependency directories from link checking
  ([`88fa985`](https://github.com/OO-LD/coregraft/commit/88fa98500ae85854f4233e6313fb2cfcaa81dd76))

### Build System

- Check untracked files locally and add a ci target
  ([`976fd55`](https://github.com/OO-LD/coregraft/commit/976fd552ddb3bacc2294a2b14a1ad30f3a30abcd))

### Testing

- Verify both generation paths produce identical output
  ([`cc28870`](https://github.com/OO-LD/coregraft/commit/cc28870fbf1f6e83af72d01a5ce766597e2df627))


## v0.8.0 (2026-08-10)

### Features

- **ci**: Add template backport workflow and instance registry
  ([`3348e58`](https://github.com/OO-LD/coregraft/commit/3348e58a6148c6daeda0b8293805c54e30f55f2f))


## v0.7.0 (2026-08-10)

### Bug Fixes

- **template**: Keep generated files clean when a marker block is stripped
  ([`7c4b5dd`](https://github.com/OO-LD/coregraft/commit/7c4b5dd627651f580bf82232bbac922d2e5a232d))

### Features

- **template**: Add optional citation, docker, devcontainer and benchmark layers
  ([`75c2c70`](https://github.com/OO-LD/coregraft/commit/75c2c70a11fb10134c87b9baaceee8980c11c4ac))


## v0.6.0 (2026-08-10)

### Bug Fixes

- **ci**: Ignore staged schema links in the link checker
  ([`8d2b658`](https://github.com/OO-LD/coregraft/commit/8d2b658a43ac9c103e41ab1789c2e489f5a1e440))

- **profile**: Add ruff configuration to the schema profile
  ([`61b8030`](https://github.com/OO-LD/coregraft/commit/61b803082f5f958876d6a0f3ebd871223eb9430f))

### Features

- **profile**: Add schema profile overlay
  ([`a7dbcd7`](https://github.com/OO-LD/coregraft/commit/a7dbcd7e81e7fb5a0519a52cce484a50f37f3ae6))


## v0.5.0 (2026-08-10)

### Features

- **profile**: Add python profile overlay
  ([`6810909`](https://github.com/OO-LD/coregraft/commit/68109094b5a7d509dc53fa82cc52db99471c7696))


## v0.4.0 (2026-08-10)

### Features

- **template**: Add make init bootstrap
  ([`0b56c33`](https://github.com/OO-LD/coregraft/commit/0b56c33d3f25e844035c0dfff3a4d90027cda15b))


## v0.3.0 (2026-08-10)

### Documentation

- Add contributing guide, issue forms and pull request template
  ([`c6f3102`](https://github.com/OO-LD/coregraft/commit/c6f31023d3d4f091214fcbebc84d6752b6b5b4c2))

### Features

- **template**: Add copier questionnaire and answers file
  ([`f999c3f`](https://github.com/OO-LD/coregraft/commit/f999c3f9edd5635310d2229defe565e8fb89de71))


## v0.2.0 (2026-08-10)

### Features

- **docs**: Add zensical docs with macros and versioned deploy
  ([`fa0d079`](https://github.com/OO-LD/coregraft/commit/fa0d0795a7469006f3756551bfead7c8bc8f533e))


## v0.1.0 (2026-08-10)

- Initial Release
