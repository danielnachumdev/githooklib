DELEGATOR_SCRIPT_TEMPLATE: str = """#!/usr/bin/env python3

import sys
from pathlib import Path


def find_project_root(module_name):
    module_path_parts = module_name.split(".")
    module_file_path = Path(*module_path_parts).with_suffix(".py")
    
    current = Path(__file__).resolve()
    for path in [current] + list(current.parents):
        resolved_path = path.resolve()
        module_file = resolved_path / module_file_path
        if module_file.exists() and (resolved_path / "githooklib").exists():
            return resolved_path
    return None


def main():
    import os
    import logging
    module_name = "{module_name}"
    project_root = find_project_root(module_name)
    if not project_root:
        print("Error: Could not find project root containing " + module_name, file=sys.stderr)
        module_file_path = "/".join(module_name.split(".")) + ".py"
        print("Looked for module file: " + module_file_path, file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, str(project_root))
    from {module_name} import {class_name}
    debug = os.getenv("GITHOOKLIB_DEBUG", "").lower() in ("1", "true", "yes")
    log_level = logging.DEBUG if debug else None
    hook = {class_name}(log_level=log_level)
    exit_code = hook.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
"""

__all__ = ["DELEGATOR_SCRIPT_TEMPLATE"]
