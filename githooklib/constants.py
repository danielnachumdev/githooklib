EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1

DELEGATOR_SCRIPT_TEMPLATE: str = f"""#!/usr/bin/env python3

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def find_git_root_via_command() -> Optional[Path]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip()).resolve()
        if (git_root / ".git").exists():
            return git_root
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def find_project_root() -> Optional[Path]:
    git_root = find_git_root_via_command()
    if not git_root:
        return None
    
    return git_root.parent


def _is_debug_enabled() -> bool:
    debug_env = os.getenv("GITHOOKLIB_DEBUG", "").lower()
    return debug_env in ("1", "true", "yes")


def _get_log_level() -> Optional[int]:
    return logging.DEBUG if _is_debug_enabled() else None


def _print_error_and_exit(module_name: str) -> None:
    module_file_path = "/".join(module_name.split(".")) + ".py"
    error_message = f"Error: Could not find project root containing {{module_name}}"
    file_message = "Looked for module file: " + module_file_path
    print(error_message, file=sys.stderr)
    print(file_message, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    module_name = "{{module_name}}"
    
    project_root = find_project_root()
    if not project_root:
        _print_error_and_exit(module_name)
    
    sys.path.insert(0, str(project_root))
    from {{module_name}} import {{class_name}}
    
    log_level = _get_log_level()
    hook = {{class_name}}(log_level=log_level)
    exit_code = hook.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
"""

__all__ = ["EXIT_SUCCESS", "EXIT_FAILURE", "DELEGATOR_SCRIPT_TEMPLATE"]
