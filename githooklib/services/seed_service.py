import shutil
from pathlib import Path
from typing import Optional

from ..definitions import SeedFailureDetails
from ..constants import TARGET_HOOKS_DIR
from ..gateways.seed_gateway import SeedGateway
from ..logger import get_logger

logger = get_logger()


class HookSeedingService:

    def __init__(self) -> None:
        self.examples_gateway = SeedGateway()

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


__all__ = ["HookSeedingService", "SeedGateway", "SeedFailureDetails"]
