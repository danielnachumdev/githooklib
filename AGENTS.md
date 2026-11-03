# githooklib – Agent Context

Implementation guide for coding agents. Product pitch: [`README.md`](README.md).

## Orientation

| Item | Detail |
| ---- | ------ |
| Package | Python library on PyPI (`githooklib/`) |
| Toolchain | [uv](https://docs.astral.sh/uv/) + `pyproject.toml` / `uv.lock` |
| Python | `>=3.8` |
| CI/CD | [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) `@v1` |

Do not commit secrets (`.pypirc`, API tokens). Publishing is via semver-cd + PyPI — no local `quickpub` / `publish.py`.

## Develop

```bash
uv sync                 # runtime only → .venv
uv sync --group dev     # + pytest, black, …
uv run pytest
```

`tool.uv.default-groups` is empty — `uv sync` does **not** install `dev` by default. CI uses `uv sync --group dev`.

## PRs / releases

1. Exactly one label: `noBump` | `bumpPatch` | `bumpMinor` | `bumpMajor`.
2. Required checks: **CI / CI**, **Semver / Semver**.
3. CD: GitHub Release + PyPI (`publish-pypi: true`). Needs secret `PYPI_API_TOKEN`.
4. Dependabot opens PRs with `noBump`; maintainers merge.

Shared how-to: [actions HOW-TO-USE](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md).
