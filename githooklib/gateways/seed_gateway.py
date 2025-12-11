from functools import lru_cache
from pathlib import Path
from typing import List

from ..constants import EXAMPLES_DIR


class SeedGateway:

    def _get_githooklib_path(self) -> Path:
        return Path(__file__).parent.parent

    def _get_examples_folder_path(self) -> Path:
        return self._get_githooklib_path() / EXAMPLES_DIR

    @lru_cache
    def get_available_examples(self) -> List[str]:
        examples_path = self._get_examples_folder_path()
        if not examples_path.exists():
            return []

        example_files = [
            f.stem for f in examples_path.glob("*.py") if f.name != "__init__.py"
        ]
        return sorted(example_files)

    @lru_cache
    def is_example_available(self, example_name: str) -> bool:
        examples_path = self._get_examples_folder_path()
        source_file = examples_path / f"{example_name}.py"
        return source_file.exists()

    @lru_cache
    def get_example_path(self, example_name: str) -> Path:
        return self._get_examples_folder_path() / f"{example_name}.py"


__all__ = [
    "SeedGateway",
]
