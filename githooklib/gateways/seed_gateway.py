from functools import lru_cache
from pathlib import Path
from typing import List

from ..constants import EXAMPLES_DIR
from ..logger import get_logger
from ..utils.singleton import singleton

logger = get_logger()


@singleton
class SeedGateway:

    @lru_cache
    def _get_githooklib_path(self) -> Path:
        path = Path(__file__).parent.parent
        logger.trace("Githooklib path: %s", path)
        return path

    @lru_cache
    def _get_examples_folder_path(self) -> Path:
        examples_path = self._get_githooklib_path() / EXAMPLES_DIR
        logger.trace("Examples folder path: %s", examples_path)
        return examples_path

    @lru_cache
    def get_available_examples(self) -> List[str]:
        logger.debug("Getting available examples")
        examples_path = self._get_examples_folder_path()
        logger.trace("Examples path: %s", examples_path)
        if not examples_path.exists():
            logger.debug("Examples path does not exist: %s", examples_path)
            return []

        logger.trace("Searching for Python files in examples directory")
        example_files = [
            f.stem for f in examples_path.glob("*.py") if f.name != "__init__.py"
        ]
        sorted_examples = sorted(example_files)
        logger.debug("Found %d available examples", len(sorted_examples))
        logger.trace("Available examples: %s", sorted_examples)
        return sorted_examples

    @lru_cache
    def is_example_available(self, example_name: str) -> bool:
        logger.debug("Checking if example '%s' is available", example_name)
        examples_path = self._get_examples_folder_path()
        source_file = examples_path / f"{example_name}.py"
        logger.trace("Checking for example file: %s", source_file)
        exists = source_file.exists()
        logger.debug("Example '%s' available: %s", example_name, exists)
        return exists

    @lru_cache
    def get_example_path(self, example_name: str) -> Path:
        logger.debug("Getting example path for '%s'", example_name)
        examples_path = self._get_examples_folder_path()
        example_path = examples_path / f"{example_name}.py"
        logger.trace("Example path: %s", example_path)
        return example_path


__all__ = [
    "SeedGateway",
]
