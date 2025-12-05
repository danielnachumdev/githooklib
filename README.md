# githooklib

A Python framework for creating, managing, and installing Git hooks with automatic discovery and CLI tools.

## Features

- **Easy Hook Creation**: Subclass `GitHook` to create custom Git hooks with minimal boilerplate
- **Automatic Discovery**: Automatically finds hooks in your project from `githooks/` directory or `*_hook.py` files
- **CLI Tools**: Command-line interface for listing, installing, uninstalling, and running hooks
- **Built-in Utilities**: Includes logger, command executor, and Git context management
- **Project-Aware**: Automatically finds project root and handles module imports correctly

## Installation

```bash
pip install githooklib
```

## Quick Start

### 1. Create a Git Hook

Create a hook by subclassing `GitHook` in a `githooks/` directory:

```python
# githooks/pre_push.py
from githooklib import GitHook, HookResult, GitHookContext


class PrePushHook(GitHook):
    def __init__(self):
        super().__init__(hook_name="pre-push")

    def execute(self, context: GitHookContext) -> HookResult:
        # Your hook logic here
        self.logger.info("Running pre-push checks...")

        # Example: Check if tests pass
        result = self.command_executor.run(["python", "-m", "pytest"])
        if not result.success:
            return HookResult(
                success=False,
                message="Tests failed. Push aborted.",
                exit_code=1
            )

        return HookResult(success=True, message="All checks passed!")
```

### 2. Install the Hook

Use the CLI to install your hook:

```bash
python -m githooklib install pre-push
```

Or use the Python API:

```python
from githooks.pre_push import PrePushHook

hook = PrePushHook()
hook.install()
```

### 3. Verify Installation

```bash
python -m githooklib show
```

## CLI Usage

The `githooklib` CLI provides several commands for managing hooks:

### List Available Hooks

```bash
python -m githooklib list
```

### Show Installed Hooks

```bash
python -m githooklib show
```

### Install a Hook

```bash
python -m githooklib install <hook-name>
```

### Uninstall a Hook

```bash
python -m githooklib uninstall <hook-name>
```

### Run a Hook Manually (for testing)

```bash
python -m githooklib run <hook-name>
```

With debug logging:

```bash
python -m githooklib run <hook-name> --debug
```

### Custom Hook Search Paths

By default, hooks are discovered from the `githooks/` directory. You can specify custom paths:

```bash
python -m githooklib --hook-paths custom_hooks other_hooks list
```

## Creating Hooks

### Hook Structure

All hooks must:
1. Subclass `GitHook`
2. Call `super().__init__()` with a `hook_name` parameter
3. Implement the `execute(context: GitHookContext) -> HookResult` method

### Hook Discovery

Hooks are automatically discovered from:
- Files in the `githooks/` directory (default)
- Root-level files matching `*_hook.py` pattern (backward compatibility)

The hook name is determined by the `hook_name` parameter passed to `GitHook.__init__()`, not the filename.

### Example: Pre-commit Hook

```python
# githooks/pre_commit.py
from githooklib import GitHook, HookResult, GitHookContext


class PreCommitHook(GitHook):
    def __init__(self):
        super().__init__(hook_name="pre-commit")

    def execute(self, context: GitHookContext) -> HookResult:
        # Run linter
        lint_result = self.command_executor.run(["flake8", "."])
        if not lint_result.success:
            return HookResult(
                success=False,
                message="Linting failed. Commit aborted.",
                exit_code=1
            )

        # Run formatter check
        format_result = self.command_executor.run(["black", "--check", "."])
        if not format_result.success:
            return HookResult(
                success=False,
                message="Code formatting check failed. Run 'black .' to fix.",
                exit_code=1
            )

        self.logger.success("All pre-commit checks passed!")
        return HookResult(success=True)
```

### Example: Commit Message Hook

```python
# githooks/commit_msg.py
from githooklib import GitHook, HookResult, GitHookContext


class CommitMsgHook(GitHook):
    def __init__(self):
        super().__init__(hook_name="commit-msg")

    def execute(self, context: GitHookContext) -> HookResult:
        # Get commit message from stdin (first line)
        commit_msg = context.get_stdin_line(0, "")

        if not commit_msg:
            return HookResult(
                success=False,
                message="Empty commit message",
                exit_code=1
            )

        # Enforce commit message format (e.g., must start with issue number)
        if not commit_msg.startswith("#"):
            return HookResult(
                success=False,
                message="Commit message must start with issue number (e.g., '#123: ...')",
                exit_code=1
            )

        return HookResult(success=True)
```

## API Reference

### GitHook

The base class for all Git hooks.

#### Methods

- `execute(context: GitHookContext) -> HookResult`: Abstract method that must be implemented. Contains your hook logic.
- `install() -> bool`: Install the hook to `.git/hooks/`
- `uninstall() -> bool`: Remove the hook from `.git/hooks/`
- `run() -> int`: Execute the hook (called by Git automatically)

#### Attributes

- `hook_name`: The name of the Git hook (e.g., "pre-commit", "pre-push")
- `logger`: A `Logger` instance for logging messages
- `command_executor`: A `CommandExecutor` instance for running shell commands

### GitHookContext

Provides context information when a hook is executed.

#### Attributes

- `hook_name`: The name of the hook being executed
- `stdin_lines`: List of lines read from stdin (Git passes data via stdin)
- `project_root`: Path to the project root directory

#### Methods

- `get_stdin_line(index: int, default: Optional[str] = None) -> Optional[str]`: Get a specific line from stdin
- `has_stdin() -> bool`: Check if stdin contains data

### HookResult

Return value from `execute()` method.

#### Attributes

- `success`: Whether the hook passed (bool)
- `message`: Optional message to display (str)
- `exit_code`: Exit code (0 for success, non-zero for failure)

### CommandExecutor

Utility for executing shell commands.

```python
result = self.command_executor.run(["python", "-m", "pytest"])
if result.success:
    print(f"Output: {result.stdout}")
else:
    print(f"Error: {result.stderr}")
```

### Logger

Utility for logging messages with automatic stream routing (stdout/stderr).

```python
self.logger.info("Information message")
self.logger.success("Success message")
self.logger.warning("Warning message")
self.logger.error("Error message")
self.logger.debug("Debug message")
```

## Requirements

- Python 3.8+

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Homepage

https://github.com/danielnachumdev/githooklib

