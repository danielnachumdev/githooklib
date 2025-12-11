# pylint: disable=invalid-name
import logging
import os
import platform
import sys
from unittest.mock import patch

from githooklib.gateways import ProjectRootGateway
from githooklib import get_logger
from githooklib.logger import TRACE

logger = get_logger(__name__)


def _setup_logging() -> None:
    if "--trace" in sys.argv:
        logger.setLevel(TRACE)
        sys.argv.remove("--trace")
    elif "--debug" in sys.argv:
        logger.setLevel(logging.DEBUG)
        sys.argv.remove("--debug")
    else:
        logger.setLevel(logging.INFO)


if platform.system() != "Windows":
    os.environ["PAGER"] = "cat"
    os.environ["INTERACTIVE"] = "False"

import fire
import fire.value_types

from .cli import CLI
from .utils import FireGetResultMock


def main() -> None:
    _setup_logging()
    logger.trace("platform: %s", platform.platform())
    logger.trace("interpreter: %s", sys.executable)
    root = ProjectRootGateway.find_project_root()
    if not root:
        logger.error("Could not find project root")
        sys.exit(1)
    logger.debug("CWD: %s", root)
    original_function = fire.trace.FireTrace.GetResult
    mock_function = FireGetResultMock(original_function)
    try:
        with patch("fire.trace.FireTrace.GetResult", mock_function):
            code = fire.Fire(CLI)
    except Exception:  # pylint: disable=broad-except
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
        sys.exit(1)

    sys.exit(code if isinstance(code, int) else 0)


if __name__ == "__main__":
    main()


__all__ = ["main"]
