# githooklib

**Python Git hooks as classes** — write `pre-commit` / `pre-push` (and friends) in Python, auto-discover them from `githooks/`, and install them with a small CLI.

[![CI](https://github.com/danielnachumdev/githooklib/actions/workflows/ci.yml/badge.svg)](https://github.com/danielnachumdev/githooklib/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/githooklib.svg)](https://pypi.org/project/githooklib/)
[![Python](https://img.shields.io/pypi/pyversions/githooklib.svg)](https://pypi.org/project/githooklib/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Requires **Python 3.8+**.

## Why githooklib?

Shell one-liners and opaque hook managers make project checks hard to test and share. **githooklib** keeps hooks as normal Python classes: subclass `GitHook`, drop the file under `githooks/`, install once, and run the same code from Git or the CLI.

- **Class-based hooks** with `execute(context) -> HookResult`
- **Automatic discovery** from a project `githooks/` directory
- **CLI** to list, install, uninstall, run, and seed example hooks
- **Conditional runs** via `get_file_patterns()` (glob / fnmatch)
- **MIT licensed**, tested with pytest

## Install

```bash
pip install githooklib
# or
uv add githooklib
```

Entry points: `githooklib` and `githooks` (same CLI).

## Quick start

### 1. Create a hook

```python
# githooks/pre_commit.py
from typing import List, Optional

from githooklib import GitHook, GitHookContext, HookResult


class PreCommitHook(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"

    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return None  # always run; or e.g. ["*.py"]

    def execute(self, context: GitHookContext) -> HookResult:
        self.logger.info("Running pre-commit checks...")
        result = self.command_executor.run(["python", "-m", "pytest"])
        if not result.success:
            return HookResult(
                success=False,
                message="Tests failed. Commit aborted.",
                exit_code=1,
            )
        return HookResult(success=True, message="All checks passed!")
```

### 2. Install and use

```bash
githooklib install pre-commit
githooklib list
githooklib run pre-commit --debug
```

### 3. Seed an example

```bash
githooklib seed                 # list packaged examples
githooklib seed pre_commit_black
```

## CLI

```bash
githooklib list                     # available hooks in this project
githooklib show                     # installed hooks (+ source)
githooklib install <hook-name>
githooklib uninstall <hook-name>
githooklib run <hook-name> [--debug]
githooklib seed [example-name]
```

## What you get

| Surface | Role |
| -------- | ---- |
| `GitHook` | Abstract base: `get_hook_name`, `get_file_patterns`, `execute` |
| `GitHookContext` | Hook name, argv, project root, stdin lines, `get_changed_files()` |
| `HookResult` / `CommandResult` | Structured success, message, exit code, command output |
| `CommandExecutor` | Run shell / `python -m` from hooks (`self.command_executor`) |
| CLI / `API` | Discover, install, uninstall, run, seed |

Subclass contract:

- **`get_hook_name()`** — Git hook name (`pre-commit`, `pre-push`, …)
- **`get_file_patterns()`** — `None` / `[]` = always; else fnmatch globs on changed files
- **`execute(context)`** — return `HookResult`; use `self.logger` and `self.command_executor`

## Contributing & development

Agent/developer workflow (uv, tests, CI/CD labels, secrets): see [`AGENTS.md`](./AGENTS.md).

Report security issues privately via [GitHub advisories](https://github.com/danielnachumdev/githooklib/security/advisories/new).

## License

MIT — see [`LICENSE`](./LICENSE).
