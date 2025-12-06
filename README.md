# githooklib

A Python framework for creating, managing, and installing Git hooks with automatic discovery and CLI tools.

## Installation

```bash
pip install githooklib
```

## Quick Start

### 1. Create a Hook

Create a hook by subclassing `GitHook` in a `githooks/` directory:

```python
# githooks/pre_commit.py
from githooklib import GitHook, HookResult, GitHookContext


class PreCommitHook(GitHook):
    @property
    def hook_name(self) -> str:
        return "pre-commit"

    def execute(self, context: GitHookContext) -> HookResult:
        self.logger.info("Running pre-commit checks...")
        result = self.command_executor.run(["python", "-m", "pytest"])
        if not result.success:
            return HookResult(
                success=False,
                message="Tests failed. Commit aborted.",
                exit_code=1
            )
        return HookResult(success=True, message="All checks passed!")
```

### 2. Install the Hook

```bash
githooklib install pre-commit
```

### 3. Seed Example Hooks

```bash
githooklib seed                    # List available examples
githooklib seed pre_commit_black   # Seed an example
```

## CLI Commands

```bash
githooklib list                    # List available hooks
githooklib show                    # Show installed hooks
githooklib install <hook-name>     # Install a hook
githooklib uninstall <hook-name>   # Uninstall a hook
githooklib run <hook-name>         # Run a hook manually
githooklib run <hook-name> --debug # Run with debug logging
githooklib seed [example-name]     # Seed example hooks
```

## API Reference

### GitHook

Base class for all Git hooks. Subclass and implement:

- `hook_name` (property): The name of the Git hook (e.g., "pre-commit", "pre-push")
- `execute(context: GitHookContext) -> HookResult`: Your hook logic

Available attributes:
- `logger`: Logger instance for logging messages
- `command_executor`: CommandExecutor instance for running shell commands

### GitHookContext

Provides context when a hook is executed:

- `hook_name`: The name of the hook being executed
- `stdin_lines`: List of lines from stdin
- `project_root`: Path to the project root
- `get_stdin_line(index: int, default: Optional[str]) -> Optional[str]`: Get a specific line from stdin
- `has_stdin() -> bool`: Check if stdin contains data

### HookResult

Return value from `execute()`:

- `success`: Whether the hook passed (bool)
- `message`: Optional message to display (str)
- `exit_code`: Exit code (0 for success, non-zero for failure)

## Requirements

- Python 3.8+

## License

See LICENSE file for details.

## Homepage

https://github.com/danielnachumdev/githooklib
