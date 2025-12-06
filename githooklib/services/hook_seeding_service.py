import shutil
from pathlib import Path
from typing import Optional

from ..gateways.project_root_gateway import ProjectRootGateway


class HookSeedingService:
    EXAMPLES_DIR = "examples"
    TARGET_HOOKS_DIR = "githooks"

    def __init__(self, project_root_gateway: ProjectRootGateway) -> None:
        self.project_root_gateway = project_root_gateway

    def get_examples_path(self) -> Path:
        package_dir = Path(__file__).parent.parent
        return package_dir / self.EXAMPLES_DIR

    def get_available_examples(self) -> list[str]:
        examples_path = self.get_examples_path()
        if not examples_path.exists():
            return []

        example_files = [
            f.stem for f in examples_path.glob("*.py") if f.name != "__init__.py"
        ]
        return sorted(example_files)

    def is_example_available(self, example_name: str) -> bool:
        examples_path = self.get_examples_path()
        source_file = examples_path / f"{example_name}.py"
        return source_file.exists()

    def get_target_hook_path(
        self, example_name: str, target_project_root: Optional[Path] = None
    ) -> Optional[Path]:
        project_root = (
            target_project_root or self.project_root_gateway.find_project_root()
        )
        if not project_root:
            return None
        return project_root / self.TARGET_HOOKS_DIR / f"{example_name}.py"

    def does_target_hook_exist(
        self, example_name: str, target_project_root: Optional[Path] = None
    ) -> bool:
        target_path = self.get_target_hook_path(example_name, target_project_root)
        return target_path is not None and target_path.exists()

    def seed_hook(
        self, example_name: str, target_project_root: Optional[Path] = None
    ) -> bool:
        project_root = (
            target_project_root or self.project_root_gateway.find_project_root()
        )
        if not project_root:
            return False

        if not self.is_example_available(example_name):
            return False

        if self.does_target_hook_exist(example_name, target_project_root):
            return False

        examples_path = self.get_examples_path()
        source_file = examples_path / f"{example_name}.py"
        target_hooks_dir = project_root / self.TARGET_HOOKS_DIR
        target_hooks_dir.mkdir(exist_ok=True)
        target_file = target_hooks_dir / f"{example_name}.py"

        shutil.copy2(source_file, target_file)
        return True


__all__ = ["HookSeedingService"]
