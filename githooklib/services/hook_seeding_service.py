import shutil
from pathlib import Path
from typing import Optional

from ..gateways.project_root_gateway import ProjectRootGateway


class HookSeedingService:
    EXAMPLES_DIR = "examples"
    TARGET_HOOKS_DIR = "githooks"

    def __init__(self, project_root_gateway: ProjectRootGateway):
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

    def seed_hook(
        self, example_name: str, target_project_root: Optional[Path] = None
    ) -> bool:
        project_root = (
            target_project_root or self.project_root_gateway.find_project_root()
        )
        if not project_root:
            return False

        examples_path = self.get_examples_path()
        source_file = examples_path / f"{example_name}.py"

        if not source_file.exists():
            return False

        target_hooks_dir = project_root / self.TARGET_HOOKS_DIR
        target_hooks_dir.mkdir(exist_ok=True)

        target_file = target_hooks_dir / f"{example_name}.py"

        if target_file.exists():
            return False

        shutil.copy2(source_file, target_file)
        return True
