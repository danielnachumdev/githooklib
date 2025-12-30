import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..constants import EXIT_FAILURE
from ..gateways.git_gateway import GitGateway
from ..logger import get_logger
from ..utils.singleton import singleton
from .hook_discovery_service import HookDiscoveryService

logger = get_logger()


@dataclass
class InstalledHooksContext:
    installed_hooks: Dict[str, bool]
    git_root: Optional[Path]
    hooks_dir_exists: bool


@singleton
class HookManagementService:
    def __init__(self) -> None:
        self.hook_discovery_service = HookDiscoveryService()
        self.git_gateway = GitGateway()
        logger.trace("HookManagementService initialized")

    def list_hooks(self) -> List[str]:
        hooks = self.hook_discovery_service.discover_hooks()
        hook_names = sorted(hooks.keys())
        return hook_names

    def install_hook(self, hook_name: str) -> bool:
        logger.debug("Installing hook '%s'", hook_name)
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            logger.debug("Hook '%s' not available for installation", hook_name)
            return False
        hook_class = hooks[hook_name]
        logger.trace("Hook class for '%s': %s", hook_name, hook_class.__name__)
        hook = hook_class()
        logger.debug("Calling install() on hook '%s'", hook_name)
        success = hook.install()
        logger.debug("Hook '%s' installation result: %s", hook_name, success)
        return success

    def uninstall_hook(self, hook_name: str) -> bool:
        logger.debug("Uninstalling hook '%s'", hook_name)
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            logger.debug("Hook '%s' not available for uninstallation", hook_name)
            return False
        hook_class = hooks[hook_name]
        logger.trace("Hook class for '%s': %s", hook_name, hook_class.__name__)
        hook = hook_class()
        logger.debug("Calling uninstall() on hook '%s'", hook_name)
        success = hook.uninstall()
        logger.debug("Hook '%s' uninstallation result: %s", hook_name, success)
        return success

    def run_hook(self, hook_name: str) -> int:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            logger.warning("Hook '%s' not found in discovered hooks", hook_name)
            logger.debug("Hook '%s' not available for execution", hook_name)
            return EXIT_FAILURE
        hook_class = hooks[hook_name]
        logger.trace("Hook class for '%s': %s", hook_name, hook_class.__name__)
        hook = hook_class()
        exit_code = hook.run()
        return exit_code

    def get_installed_hooks_with_context(self) -> InstalledHooksContext:
        logger.debug("Getting installed hooks with context")
        git_root = self.git_gateway.get_git_root_path()
        logger.trace("Git root: %s", git_root)
        if not git_root:
            logger.debug("No git root found, returning empty context")
            return InstalledHooksContext({}, None, False)

        hooks_dir = git_root / "hooks"
        hooks_dir_exists = hooks_dir.exists()
        logger.trace("Hooks directory: %s, exists: %s", hooks_dir, hooks_dir_exists)

        if not hooks_dir_exists:
            logger.debug("Hooks directory does not exist")
            return InstalledHooksContext({}, git_root, False)

        logger.debug("Getting installed hooks from directory: %s", hooks_dir)
        installed_hooks = self.git_gateway.get_installed_hooks(hooks_dir)
        logger.debug("Found %d installed hooks", len(installed_hooks))
        logger.trace("Installed hooks: %s", installed_hooks)
        return InstalledHooksContext(installed_hooks, git_root, True)


__all__ = ["HookManagementService", "InstalledHooksContext"]
