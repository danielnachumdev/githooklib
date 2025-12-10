import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..logger import get_logger

logger = get_logger()

EXAMPLES_DIR = "examples"
TARGET_HOOKS_DIR = "githooks"


@dataclass
class SeedFailureDetails:
    example_not_found: bool
    project_root_not_found: bool
    target_hook_already_exists: bool
    target_hook_path: Optional[Path]
    available_examples: List[str]


class ExamplesGateway:

    def _get_githooklib_path(self) -> Path:
        return Path(__file__).parent.parent

    def _get_examples_folder_path(self) -> Path:
        return self._get_githooklib_path() / EXAMPLES_DIR

    def get_available_examples(self) -> List[str]:
        examples_path = self._get_examples_folder_path()
        if not examples_path.exists():
            return []

        example_files = [
            f.stem for f in examples_path.glob("*.py") if f.name != "__init__.py"
        ]
        return sorted(example_files)

    def is_example_available(self, example_name: str) -> bool:
        examples_path = self._get_examples_folder_path()
        source_file = examples_path / f"{example_name}.py"
        return source_file.exists()

    def get_example_path(self, example_name: str) -> Path:
        return self._get_examples_folder_path() / f"{example_name}.py"


class HookSeedingService:

    def __init__(self) -> None:
        self.examples_gateway = ExamplesGateway()

    def get_target_hook_path(self, example_name: str, project_root: Path) -> Path:
        return project_root / TARGET_HOOKS_DIR / f"{example_name}.py"

    def does_target_hook_exist(self, example_name: str, project_root: Path) -> bool:
        return self.get_target_hook_path(example_name, project_root).exists()

    def seed_hook(self, example_name: str, project_root: Path) -> bool:
        if not self.examples_gateway.is_example_available(example_name):
            logger.warning("Example '%s' is not available", example_name)
            return False

        if self.does_target_hook_exist(example_name, project_root):
            logger.warning("Target hook '%s' already exists", example_name)
            return False

        source_file = self.examples_gateway.get_example_path(example_name)
        target_hooks_dir = project_root / TARGET_HOOKS_DIR
        target_hooks_dir.mkdir(exist_ok=True)
        target_file = target_hooks_dir / f"{example_name}.py"

        shutil.copy2(source_file, target_file)
        logger.info("Successfully seeded hook '%s' to %s", example_name, target_file)
        return True

    def get_seed_failure_details(
        self, example_name: str, project_root: Optional[Path]
    ) -> SeedFailureDetails:
        example_not_found = not self.examples_gateway.is_example_available(example_name)
        project_root_not_found = project_root is None
        target_hook_path = (
            self.get_target_hook_path(example_name, project_root)
            if project_root
            else None
        )
        target_hook_already_exists = (
            self.does_target_hook_exist(example_name, project_root)
            if project_root
            else False
        )
        available_examples = self.examples_gateway.get_available_examples()

        return SeedFailureDetails(
            example_not_found=example_not_found,
            project_root_not_found=project_root_not_found,
            target_hook_already_exists=target_hook_already_exists,
            target_hook_path=target_hook_path,
            available_examples=available_examples,
        )


__all__ = ["HookSeedingService", "ExamplesGateway", "SeedFailureDetails"]
