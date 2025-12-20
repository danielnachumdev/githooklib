import shutil
from pathlib import Path
from typing import Optional

from ..definitions import SeedFailureDetails
from ..constants import TARGET_HOOKS_DIR
from ..gateways.seed_gateway import SeedGateway
from ..logger import get_logger
from ..utils.singleton import singleton

logger = get_logger()


@singleton
class HookSeedingService:

    def __init__(self) -> None:
        self.examples_gateway = SeedGateway()
        logger.trace("HookSeedingService initialized")

    def get_target_hook_path(self, example_name: str, project_root: Path) -> Path:
        target_path = project_root / TARGET_HOOKS_DIR / f"{example_name}.py"
        logger.trace("Target hook path for '%s': %s", example_name, target_path)
        return target_path

    def does_target_hook_exist(self, example_name: str, project_root: Path) -> bool:
        target_path = self.get_target_hook_path(example_name, project_root)
        exists = target_path.exists()
        logger.debug("Target hook '%s' exists: %s", example_name, exists)
        logger.trace("Target path: %s", target_path)
        return exists

    def seed_hook(self, example_name: str, project_root: Path) -> bool:
        logger.debug(
            "Seeding hook '%s' to project root: %s", example_name, project_root
        )
        if not self.examples_gateway.is_example_available(example_name):
            logger.warning("Example '%s' is not available", example_name)
            logger.debug("Example '%s' not found in examples", example_name)
            return False

        if self.does_target_hook_exist(example_name, project_root):
            logger.warning("Target hook '%s' already exists", example_name)
            logger.debug("Target hook '%s' already exists, cannot seed", example_name)
            return False

        source_file = self.examples_gateway.get_example_path(example_name)
        logger.trace("Source file: %s", source_file)
        target_hooks_dir = project_root / TARGET_HOOKS_DIR
        logger.trace("Target hooks directory: %s", target_hooks_dir)
        logger.debug("Creating target hooks directory if it doesn't exist")
        target_hooks_dir.mkdir(exist_ok=True)
        target_file = target_hooks_dir / f"{example_name}.py"
        logger.trace("Target file: %s", target_file)

        logger.debug("Copying example file from %s to %s", source_file, target_file)
        shutil.copy2(source_file, target_file)
        logger.info("Successfully seeded hook '%s' to %s", example_name, target_file)
        logger.debug("Hook '%s' seeding completed successfully", example_name)
        return True

    def get_seed_failure_details(
        self, example_name: str, project_root: Optional[Path]
    ) -> SeedFailureDetails:
        logger.debug("Getting seed failure details for example '%s'", example_name)
        logger.trace("Project root: %s", project_root)
        example_not_found = not self.examples_gateway.is_example_available(example_name)
        logger.trace("Example '%s' not found: %s", example_name, example_not_found)
        project_root_not_found = project_root is None
        logger.trace("Project root not found: %s", project_root_not_found)
        target_hook_path = (
            self.get_target_hook_path(example_name, project_root)
            if project_root
            else None
        )
        logger.trace("Target hook path: %s", target_hook_path)
        target_hook_already_exists = (
            self.does_target_hook_exist(example_name, project_root)
            if project_root
            else False
        )
        logger.trace("Target hook already exists: %s", target_hook_already_exists)
        available_examples = self.examples_gateway.get_available_examples()
        logger.trace("Available examples: %s", available_examples)

        details = SeedFailureDetails(
            example_not_found=example_not_found,
            project_root_not_found=project_root_not_found,
            target_hook_already_exists=target_hook_already_exists,
            target_hook_path=target_hook_path,
            available_examples=available_examples,
        )
        logger.debug(
            "Failure details: example_not_found=%s, project_root_not_found=%s, target_hook_already_exists=%s",
            details.example_not_found,
            details.project_root_not_found,
            details.target_hook_already_exists,
        )
        return details


__all__ = ["HookSeedingService", "SeedGateway", "SeedFailureDetails"]
