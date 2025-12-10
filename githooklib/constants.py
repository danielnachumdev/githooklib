EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1
EXAMPLES_DIR: str = "examples"
TARGET_HOOKS_DIR: str = "githooks"
DEFAULT_HOOK_SEARCH_DIR = "githooks"
DELEGATOR_SCRIPT_TEMPLATE: str = """#!/usr/bin/env python3

import subprocess
import sys


def main() -> None:
    result = subprocess.run(
        ["{python_executable}", "-m", "githooklib", "run", "{hook_name}"],
        cwd="{project_root}",
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
"""

__all__ = ["EXIT_SUCCESS", "EXIT_FAILURE", "DELEGATOR_SCRIPT_TEMPLATE"]
