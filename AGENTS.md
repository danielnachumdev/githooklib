# githooklib – Agent Context

Implementation guide for coding agents changing **githooklib**. Product pitch and user-facing install: [`README.md`](README.md).

---

## Orientation

| Question | Answer |
| -------- | ------ |
| What is this? | Python framework + CLI for class-based Git hooks |
| Importable code | `githooklib/` |
| Toolchain | [uv](https://docs.astral.sh/uv/) + `pyproject.toml` / `uv.lock` |
| Python | `>=3.8` |
| Tests | `tests/` — pytest + coverage (`fail_under = 50` in `.coveragerc`); **never delete** |
| Secrets | Never commit `.pypirc`, API tokens, or credentials |

```text
.
├── .github/             # CODEOWNERS, dependabot.yml, thin CI/CD orchestrators
├── githooklib/          # Importable package (+ packaged examples/)
├── githooks/            # In-repo example / project hooks (not the PyPI package)
├── tests/               # ut/ + e2e/
├── pyproject.toml
├── uv.lock
├── README.md            # Marketing / user docs
└── LICENSE              # MIT
```

Shared CI/CD: [`danielnachumdev/actions`](https://github.com/danielnachumdev/actions) (this repo pins **`@latest`**). How to adopt: [`HOW-TO-USE.md`](https://github.com/danielnachumdev/actions/blob/v1/HOW-TO-USE.md).

---

## Develop

```bash
uv sync                 # runtime only → .venv
uv sync --group dev     # + pytest, black, …
# or: uv sync --all-groups
```

`tool.uv.default-groups` is empty — `uv sync` does **not** install `dev` by default. CI uses `uv sync --group dev`.

| Task | Command |
| ---- | ------- |
| Import smoke | `uv run python -c "import githooklib"` |
| Tests | `uv run pytest` |
| Format | `uv run black githooklib tests` |

Config for pytest / coverage / mypy / pylint lives in `pyproject.toml` and `.coveragerc`.

### Dependencies

- **Runtime:** `fire` (CLI)
- **Dev group:** pytest, pytest-cov, pytest-xdist, black, setuptools
- Prefer editing deps in `pyproject.toml` and regenerating with `uv lock` / `uv sync --group dev`

---

## Code style & domain notes

- Follow the writing-python skill when adding/refactoring modules (class-first, SRP files, no stub shims).
- Layout: **gateways** (git / import / project root / seed), **services** (discovery, management, seed, errors), **CLI** → **API** → services.
- Public re-exports from `githooklib/__init__.py` (`GitHook`, context, command, logger helpers, version helpers). `__version__` is `importlib.metadata.version("githooklib")` (fallback `"0.0.0"` if not installed).
- New hooks for consumers: subclass `GitHook` and implement **`get_hook_name`**, **`get_file_patterns`**, **`execute`**. Discovery loads modules under project `githooks/` (and related search paths).
- Packaged seed templates live in `githooklib/examples/`; repo-local hooks under top-level `githooks/` are for this project’s own use / demos.
- Install writes a **delegator script** into `.git/hooks/<name>` that invokes the installed Python/`githooklib` for that hook.
- CLI entry points: `githooklib` and `githooks` → `githooklib.__main__:main` (Fire).

---

## PRs, CI, and releases

1. Branch off `main`; open a PR into `main`.
2. Attach **exactly one** semver label: `noBump` | `bumpPatch` | `bumpMinor` | `bumpMajor`.
3. **CI** — `…/ci.yml@latest` (tests) + `…/semver-ci.yml@latest` (validate label). Prefer **`CI / CI`** and **`Semver / Semver`**.
4. **CD** — `…/semver-cd.yml@latest` after CI succeeds on `main`: bump → wheel → GitHub Release → floating `vMAJOR` → **PyPI** (`publish-pypi: true`), or skip on `noBump`.
5. Version **source of truth** is GitHub Release tags. If none yet, CD seeds from `pyproject.toml`.
6. Dependabot PRs stay on `noBump` (auto-merge workflow present).
7. Change shared CI/semver behavior in **`danielnachumdev/actions`**, not by re-vendoring here.

**PyPI:** shipped only via CD (Trusted Publishing OIDC preferred for repo + workflow `cd.yml`; optional repo secret `PYPI_API_TOKEN`). Thin CD must grant `id-token: write` and pass `PYPI_API_TOKEN` by name. There is no local `publish.py` / quickpub path.

### Repo gates (already configured)

- `.github/CODEOWNERS` — `@danielnachumdev`
- Branch protection / ruleset: required **`CI / CI`** + **`Semver / Semver`**; code-owner reviews; no force-push to `main`
- Private vulnerability reporting via GitHub Security Advisories

---

## Sensitive / ignored

Do not commit: `.pypirc`, `.venv/`, `venv/`, `dist/`, `__pycache__/`, API keys, coverage HTML (`htmlcov/`). Track `uv.lock`. Respect `.gitignore`.
