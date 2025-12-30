from typing import Tuple

EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1
EXAMPLES_DIR: str = "examples"
TARGET_HOOKS_DIR: str = "githooks"
DEFAULT_HOOK_SEARCH_DIR = "githooks"

HOOKS_WITH_STDIN: Tuple[str, ...] = (
    "pre-push",
    "pre-receive",
    "post-receive",
    "update",
    "pre-applypatch",
    "post-applypatch",
)
DELEGATOR_SCRIPT_TEMPLATE: str = f"""#!/usr/bin/env python3

import subprocess
import sys


def main() -> None:
    try:
        compat_check = subprocess.run(
            [
                "{{python_executable}}",
                "-c",
                "import githooklib; exit(0 if githooklib.is_version_compatible('{{installed_version}}') else 1)",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if compat_check.returncode != 0:
            version_info = subprocess.run(
                [
                    "{{python_executable}}",
                    "-c",
                    "import githooklib; print(githooklib.__version__ + '|' + githooklib.MINIMUM_COMPATIBLE_VERSION)",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if version_info.returncode == 0:
                current_version, min_version = version_info.stdout.strip().split("|")
                print(
                    "Version " + current_version + " of githooklib requires a minimum version of " + min_version + f" but hook was installed with version {{installed_version}}.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Hook was installed with githooklib version {{installed_version}} and is incompatible with the current version.",
                    file=sys.stderr,
                )
            sys.exit(1)

        result = subprocess.run(
            ["{{python_executable}}", "-u", "-m", "githooklib", "run", "{{hook_name}}"],
            cwd="{{project_root}}",
            stdin=sys.stdin,
            encoding="utf-8",
            errors="replace",
        )
        sys.exit(result.returncode)
    except Exception as e:
        print("Error executing hook: " + str(e), file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""

__all__ = [
    "EXIT_SUCCESS",
    "EXIT_FAILURE",
    "DELEGATOR_SCRIPT_TEMPLATE",
    "HOOKS_WITH_STDIN",
]
