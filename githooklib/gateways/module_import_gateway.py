import sys
from pathlib import Path
from typing import Optional

from .git_repository_gateway import GitRepositoryGateway


class ModuleImportGateway:
    @staticmethod
    def find_module_file(
        module_name: str, project_root: Optional[Path]
    ) -> Optional[str]:
        try:
            import importlib.util

            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                if project_root:
                    try:
                        module_path = Path(spec.origin)
                        relative_path = module_path.relative_to(project_root)
                        return str(relative_path)
                    except ValueError:
                        return spec.origin
                return spec.origin
        except (ImportError, AttributeError, ValueError):
            pass
        return None

    @staticmethod
    def convert_module_name_to_file_path(module_name: str) -> Path:
        module_path_parts = module_name.split(".")
        return Path(*module_path_parts).with_suffix(".py")

    @staticmethod
    def _add_to_sys_path_if_needed(directory: Path) -> None:
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))

    def import_module(self, module_path: Path, base_dir: Path) -> None:
        module_path = module_path.resolve()
        try:
            relative_path = module_path.relative_to(base_dir)
            self._import_relative_module(relative_path, base_dir)
        except ValueError:
            self._import_absolute_module(module_path)

    def _import_relative_module(self, relative_path: Path, base_dir: Path) -> None:
        parts = relative_path.parts[:-1] + (relative_path.stem,)
        module_name = ".".join(parts)
        self._add_to_sys_path_if_needed(base_dir)
        __import__(module_name)

    def _import_absolute_module(self, module_path: Path) -> None:
        parent_dir = module_path.parent.resolve()
        self._add_to_sys_path_if_needed(parent_dir)
        module_name = module_path.stem
        __import__(module_name)


__all__ = ["ModuleImportGateway"]
