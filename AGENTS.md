# githooklib – Agent Context

Implementation guide for coding agents. Product pitch: [`README.md`](README.md).

## Orientation

| Item | Detail |
| ---- | ------ |
| Package | Python library on PyPI |
| Toolchain | uv + `pyproject.toml` |
| CI/CD | [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) `@v1` |

## Develop

```bash
uv sync --group dev
uv run pytest -q
```

## PRs / releases

1. Exactly one label: `noBump` | `bumpPatch` | `bumpMinor` | `bumpMajor`.
2. Required checks: **CI / CI**, **Semver / Semver**.
3. CD: GitHub Release + PyPI (`publish-pypi: true`). Needs secret `PYPI_API_TOKEN`.
4. Dependabot opens PRs with `noBump`; maintainers merge.

Shared how-to: [actions HOW-TO-USE](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md).
