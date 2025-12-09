# pylint: disable=invalid-name
import logging
import os
import platform
import sys
from unittest.mock import patch

from githooklib import get_logger

if platform.system() != "Windows":
    os.environ["PAGER"] = "cat"
    os.environ["INTERACTIVE"] = "False"

import fire
import fire.value_types

from .cli import CLI
from .utils import FireGetResultMock


def get_name() -> str:
    exe = sys.argv[0]
    return "githooks" if "githooks" in exe else "githooklib"


def main() -> None:
    logger = get_logger(__file__, level=logging.DEBUG)
    logger.debug(f"Working in {os.getcwd()}")
    original_function = fire.trace.FireTrace.GetResult
    mock_function = FireGetResultMock(original_function)
    try:
        with patch("fire.trace.FireTrace.GetResult", mock_function):
            code = fire.Fire(CLI)
    except Exception:  # pylint: disable=broad-except
        sys.exit(1)

    sys.exit(code if isinstance(code, int) else 0)


if __name__ == "__main__":
    main()


__all__ = ["main"]
