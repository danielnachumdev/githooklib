import logging
from pathlib import Path
from typing import Optional

from ..git_hook import GitHook
from .hook_discovery_service import HookDiscoveryService


class HookManagementService:
    def __init__(self, hook_discovery_service: HookDiscoveryService):
        self.hook_discovery_service = hook_discovery_service

    def list_hooks(self) -> list[str]:
        hooks = self.hook_discovery_service.discover_hooks()
        return sorted(hooks.keys())

    def install_hook(self, hook_name: str) -> bool:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        return hook.install()

    def uninstall_hook(self, hook_name: str) -> bool:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            return False
        hook_class = hooks[hook_name]
        hook = hook_class()
        return hook.uninstall()

    def run_hook(self, hook_name: str, debug: bool = False) -> int:
        hooks = self.hook_discovery_service.discover_hooks()
        if hook_name not in hooks:
            return 1
        hook_class = hooks[hook_name]
        log_level = logging.DEBUG if debug else logging.INFO
        hook = hook_class(log_level=log_level)
        return hook.run()
