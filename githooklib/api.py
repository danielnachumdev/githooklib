from functools import lru_cache
from pathlib import Path
from typing import Optional

from .logger import get_logger
from .git_hook import GitHook
from .gateways import ProjectRootGateway, GitGateway, SeedGateway
from .services import (
    HookDiscoveryService,
    InstalledHooksContext,
    HookManagementService,
    ErrorMessageService,
    HookSeedingService,
    SeedFailureDetails,
)

logger = get_logger()


class API:

    def __init__(self) -> None:
        logger.trace("Initializing API")
        self.git_gateway = GitGateway()
        self.hook_discovery_service = HookDiscoveryService()
        self.hook_management_service = HookManagementService()
        self.error_message_service = ErrorMessageService()
        self.seed_service = HookSeedingService()
        self.seed_gateway = SeedGateway()

    @lru_cache
    def discover_all_hooks(self) -> dict[str, type[GitHook]]:
        logger.debug("Discovering all hooks")
        hooks = self.hook_discovery_service.discover_hooks()
        logger.trace("Discovered hooks: %s", list(hooks.keys()))
        return hooks

    @lru_cache
    def list_available_hook_names(self) -> list[str]:
        return self.hook_management_service.list_hooks()

    @lru_cache
    def check_hook_exists(self, hook_name: str) -> bool:
        exists = self.hook_discovery_service.hook_exists(hook_name)
        logger.debug("Hook '%s' exists: %s", hook_name, exists)
        return exists

    def install_hook_by_name(self, hook_name: str) -> bool:
        logger.debug("Installing hook '%s'", hook_name)
        success = self.hook_management_service.install_hook(hook_name)
        logger.debug(
            "Hook '%s' installation %s", hook_name, "succeeded" if success else "failed"
        )
        return success

    def uninstall_hook_by_name(self, hook_name: str) -> bool:
        logger.debug("Uninstalling hook '%s'", hook_name)
        success = self.hook_management_service.uninstall_hook(hook_name)
        logger.debug(
            "Hook '%s' uninstallation %s",
            hook_name,
            "succeeded" if success else "failed",
        )
        return success

    def run_hook_by_name(self, hook_name: str) -> int:
        exit_code = self.hook_management_service.run_hook(hook_name)
        logger.trace("Hook '%s' execution finished", hook_name)
        return exit_code

    def get_installed_hooks_with_context(self) -> InstalledHooksContext:
        logger.debug("Getting installed hooks with context")
        context = self.hook_management_service.get_installed_hooks_with_context()
        logger.debug("Found %d installed hooks", len(context.installed_hooks))
        logger.trace(
            "Installed hooks context: git_root=%s, hooks_dir_exists=%s",
            context.git_root,
            context.hooks_dir_exists,
        )
        return context

    def find_git_repository_root(self) -> Optional[Path]:
        logger.debug("Finding git repository root")
        git_root = self.git_gateway.get_git_root_path()
        logger.debug("Git repository root: %s", git_root)
        return git_root

    def configure_hook_search_paths(self, *hook_paths: str) -> None:
        logger.debug("Configuring hook search paths: %s", hook_paths)
        self.hook_discovery_service.set_hook_search_paths(list(hook_paths))
        logger.trace("Hook search paths configured, cache invalidated")

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        logger.debug("Getting error message for hook '%s' not found", hook_name)
        message = self.error_message_service.get_hook_not_found_error_message(hook_name)
        logger.trace("Error message: %s", message)
        return message

    def list_available_example_names(self) -> list[str]:
        logger.debug("Listing available example names")
        examples = self.seed_gateway.get_available_examples()
        logger.debug("Found %d available examples", len(examples))
        logger.trace("Available examples: %s", examples)
        return examples

    def check_example_exists(self, example_name: str) -> bool:
        logger.debug("Checking if example '%s' exists", example_name)
        exists = self.seed_gateway.is_example_available(example_name)
        logger.debug("Example '%s' exists: %s", example_name, exists)
        return exists

    def get_seed_failure_details(self, example_name: str) -> SeedFailureDetails:
        logger.debug("Getting seed failure details for example '%s'", example_name)
        try:
            project_root = ProjectRootGateway.find_project_root()
            logger.trace("Project root found: %s", project_root)
        except Exception as e:
            logger.trace("Project root not found: %s", e)
            project_root = None
        details = self.seed_service.get_seed_failure_details(example_name, project_root)
        logger.debug(
            "Seed failure details: example_not_found=%s, project_root_not_found=%s, target_hook_already_exists=%s",
            details.example_not_found,
            details.project_root_not_found,
            details.target_hook_already_exists,
        )
        return details

    def seed_example_hook_to_project(self, example_name: str) -> bool:
        logger.debug("Seeding example hook '%s' to project", example_name)
        try:
            project_root = ProjectRootGateway.find_project_root()
            logger.trace("Project root: %s", project_root)
        except Exception as e:
            logger.debug("Failed to find project root: %s", e)
            return False
        success = self.seed_service.seed_hook(example_name, project_root)
        logger.debug(
            "Example hook '%s' seeding %s",
            example_name,
            "succeeded" if success else "failed",
        )
        return success


__all__ = ["API"]
