from pathlib import Path
from typing import Optional


class ProjectRootGateway:
    def find_project_root(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / "githooklib").exists():
                return path.resolve()
        return None


__all__ = ["ProjectRootGateway"]
