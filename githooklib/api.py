from pathlib import Path
from typing import Optional

from .git_hook import GitHook
from .gateways.project_root_gateway import ProjectRootGateway
from .gateways.git_repository_gateway import GitRepositoryGateway
from .gateways.module_import_gateway import ModuleImportGateway
from .services.hook_discovery_service import HookDiscoveryService
from .services.hook_management_service import HookManagementService
from .services.error_message_service import ErrorMessageService


class API:
    DEFAULT_HOOK_SEARCH_DIR = "githooks"

    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_search_paths: Optional[list[str]] = None,
    ):
        project_root_gateway = ProjectRootGateway()
        git_repository_gateway = GitRepositoryGateway()
        module_import_gateway = ModuleImportGateway()

        self.project_root = project_root or project_root_gateway.find_project_root()
        if hook_search_paths is None:
            self.hook_search_paths = [self.DEFAULT_HOOK_SEARCH_DIR]
        else:
            self.hook_search_paths = hook_search_paths

        self.hook_discovery_service = HookDiscoveryService(
            project_root=self.project_root,
            hook_search_paths=self.hook_search_paths,
            project_root_gateway=project_root_gateway,
            module_import_gateway=module_import_gateway,
        )
        self.hook_management_service = HookManagementService(
            self.hook_discovery_service
        )
        self.error_message_service = ErrorMessageService(
            self.hook_discovery_service
        )
        self.git_repository_gateway = git_repository_gateway

    def discover_hooks(self) -> dict[str, type[GitHook]]:
        return self.hook_discovery_service.discover_hooks()

    def list_hooks(self) -> list[str]:
        return self.hook_management_service.list_hooks()

    def install_hook(self, hook_name: str) -> bool:
        return self.hook_management_service.install_hook(hook_name)

    def uninstall_hook(self, hook_name: str) -> bool:
        return self.hook_management_service.uninstall_hook(hook_name)

    def run_hook(self, hook_name: str, debug: bool = False) -> int:
        return self.hook_management_service.run_hook(hook_name, debug=debug)

    def get_installed_hooks(self) -> dict[str, bool]:
        git_root = self.git_repository_gateway.find_git_root()
        if not git_root:
            return {}
        hooks_dir = git_root / ".git" / "hooks"
        if not hooks_dir.exists():
            return {}
        return self.git_repository_gateway.get_installed_hooks(hooks_dir)

    def get_git_root(self) -> Optional[Path]:
        return self.git_repository_gateway.find_git_root()

    def set_hook_paths(self, *hook_paths: str) -> None:
        self.hook_search_paths = list(hook_paths)
        self.hook_discovery_service.set_hook_search_paths(list(hook_paths))

    def get_hook_not_found_error_message(self, hook_name: str) -> str:
        return self.error_message_service.get_hook_not_found_error_message(
            hook_name
        )


__all__ = ["API"]
