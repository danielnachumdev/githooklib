# pylint: disable=invalid-name
from .utils import FireGetResultMock
from .cli import CLI
import fire.value_types
import fire
import logging
import os
import platform
import sys
from unittest.mock import patch

from githooklib.gateways import ProjectRootGateway
from githooklib import get_logger
from githooklib.logger import TRACE
from githooklib.ui_messages import (
    UI_MESSAGE_STARTUP_INFO,
    UI_MESSAGE_COULD_NOT_FIND_PROJECT_ROOT,
)

logger = get_logger(__name__)


def _setup_logging() -> None:
    if "--trace" in sys.argv:
        logger.setLevel(TRACE)
        logger.trace("Trace logging enabled")
        sys.argv.remove("--trace")
    elif "--debug" in sys.argv:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
        sys.argv.remove("--debug")
    else:
        logger.setLevel(logging.INFO)


if platform.system() != "Windows":
    os.environ["PAGER"] = "cat"
    os.environ["INTERACTIVE"] = "False"


def main() -> None:
    _setup_logging()
    logger.info(UI_MESSAGE_STARTUP_INFO)
    logger.trace("platform: %s", platform.platform())
    logger.trace("interpreter: %s", sys.executable)
    logger.trace("sys.argv: %s", sys.argv)
    logger.debug("Finding project root")
    root = ProjectRootGateway.find_project_root()
    if not root:
        logger.error(UI_MESSAGE_COULD_NOT_FIND_PROJECT_ROOT)
        logger.debug("Project root not found, exiting")
        sys.exit(1)
    logger.debug("Project root: %s", root)
    logger.trace("Initializing Fire CLI")
    original_function = fire.trace.FireTrace.GetResult
    mock_function = FireGetResultMock(original_function)
    try:
        logger.debug("Starting CLI")
        with patch("fire.trace.FireTrace.GetResult", mock_function):
            code = fire.Fire(CLI)
        logger.debug("CLI completed with code: %s", code)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Exception in CLI: %s", e)
        logger.trace("Exception details: %s", e, exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
        logger.debug("User interrupted execution")
        sys.exit(1)

    exit_code = code if isinstance(code, int) else 0
    logger.debug("Exiting with code: %d", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


__all__ = ["main"]
