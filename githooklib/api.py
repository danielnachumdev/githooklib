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
        self.git_gateway = GitGateway()
        self.hook_discovery_service = HookDiscoveryService()
        self.hook_management_service = HookManagementService()
        self.error_message_service = ErrorMessageService()
        self.seed_service = HookSeedingService()
        self.seed_gateway = SeedGateway()

    def discover_all_hooks(self) -> dict[str, type[GitHook]]:
        return self.hook_discovery_service.discover_hooks()

    def list_available_hook_names(self) -> list[str]:
        return self.hook_management_service.list_hooks()

    def check_hook_exists(self, hook_name: str) -> bool:
        return self.hook_discovery_service.hook_exists(hook_name)

    def install_hook_by_name(self, hook_name: str) -> bool:
        return self.hook_management_service.install_hook(hook_name)

    def uninstall_hook_by_name(self, hook_name: str) -> bool:
        return self.hook_management_service.uninstall_hook(hook_name)

    def run_hook_by_name(self, hook_name: str) -> int:
        return self.hook_management_service.run_hook(hook_name)

    def get_installed_hooks_with_context(self) -> InstalledHooksContext:
        return self.hook_management_service.get_installed_hooks_with_context()

    def find_git_repository_root(self) -> Optional[Path]:
        return self.git_gateway.get_git_root_path()

    def configure_hook_search_paths(self, *hook_paths: str) -> None:
        self.hook_discovery_service.set_hook_search_paths(list(hook_paths))

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        return self.error_message_service.get_hook_not_found_error_message(hook_name)

    def list_available_example_names(self) -> list[str]:
        return self.seed_gateway.get_available_examples()

    def check_example_exists(self, example_name: str) -> bool:
        return self.seed_gateway.is_example_available(example_name)

    def get_seed_failure_details(self, example_name: str) -> SeedFailureDetails:
        try:
            project_root = ProjectRootGateway.find_project_root()
        except Exception:
            project_root = None
        return self.seed_service.get_seed_failure_details(example_name, project_root)

    def seed_example_hook_to_project(self, example_name: str) -> bool:
        try:
            project_root = ProjectRootGateway.find_project_root()
        except Exception:
            return False
        return self.seed_service.seed_hook(example_name, project_root)


__all__ = ["API"]
