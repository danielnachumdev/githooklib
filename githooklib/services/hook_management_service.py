import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..constants import EXIT_FAILURE
from ..gateways.git_gateway import GitGateway
from ..logger import get_logger
from .hook_discovery_service import HookDiscoveryService

logger = get_logger()


@dataclass
class InstalledHooksContext:
    installed_hooks: dict[str, bool]
    git_root: Optional[Path]
    hooks_dir_exists: bool


class HookManagementService:
    def __init__(self) -> None:
        self.hook_discovery_service = HookDiscoveryService()
        self.git_gateway = GitGateway()

    def list_hooks(self) -> list[str]:
        hooks = self.hook_discovery_service.discover_hooks()
        hook_names = sorted(hooks.keys())
        return hook_names

    def install_hook(self, hook_name: str) -> bool:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        success = hook.install()
        return success

    def uninstall_hook(self, hook_name: str) -> bool:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        success = hook.uninstall()
        return success

    def run_hook(self, hook_name: str) -> int:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            return EXIT_FAILURE
        hook_class = hooks[hook_name]
        hook = hook_class()
        return hook.run()

    def get_installed_hooks_with_context(self) -> InstalledHooksContext:
        git_root = self.git_gateway.get_git_root_path()
        if not git_root:
            return InstalledHooksContext({}, None, False)

        hooks_dir = git_root / "hooks"
        hooks_dir_exists = hooks_dir.exists()

        if not hooks_dir_exists:
            return InstalledHooksContext({}, git_root, False)

        installed_hooks = self.git_gateway.get_installed_hooks(hooks_dir)
        return InstalledHooksContext(installed_hooks, git_root, True)


__all__ = ["HookManagementService", "InstalledHooksContext"]
