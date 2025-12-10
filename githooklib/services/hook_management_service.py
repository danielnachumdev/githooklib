import logging
from ..constants import EXIT_FAILURE
from ..logger import get_logger
from .hook_discovery_service import HookDiscoveryService

logger = get_logger()


class HookManagementService:
    def __init__(self, hook_discovery_service: HookDiscoveryService) -> None:
        self.hook_discovery_service = hook_discovery_service

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


__all__ = ["HookManagementService"]
