from pathlib import Path
from typing import Optional


class GitRepositoryGateway:
    def find_git_root(self) -> Optional[Path]:
        current = Path.cwd()
        for path in [current] + list(current.parents):
            if (path / ".git").exists():
                return path.resolve()
        return None

    def get_installed_hooks(self, hooks_dir: Path) -> dict[str, bool]:
        installed = {}
        for hook_file in hooks_dir.iterdir():
            if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                hook_name = hook_file.name
                is_tool_installed = self._is_tool_installed_hook(hook_file)
                installed[hook_name] = is_tool_installed
        return installed

    def _is_tool_installed_hook(self, hook_path: Path) -> bool:
        try:
            content = hook_path.read_text()
            return "githooklib" in content and "find_project_root" in content
        except (OSError, IOError, UnicodeDecodeError):
            return False
