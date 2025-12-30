import logging
import sys
import unittest
from io import StringIO
from unittest.mock import patch

from githooklib.logger import (
    get_logger,
    Logger,
    StreamHandler,
    TRACE,
    SUCCESS,
)
from tests.base_test_case import BaseTestCase


class TestLogger(BaseTestCase):
    def test_get_logger_returns_logger_instance(self):
        logger = get_logger("test_module")
        self.assertIsInstance(logger, Logger)

    def test_get_logger_with_prefix(self):
        logger = get_logger("test_module_prefix", prefix="test-prefix")
        self.assertTrue(logger.propagate)
        self.assertEqual(len(logger.handlers), 1)

    def test_logger_set_level_only_affects_logger(self):
        logger = get_logger("test_module")
        logger.setLevel(logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_logger_success_method(self):
        logger = get_logger("test_module")
        logger.setLevel(SUCCESS)
        with patch.object(logging.Logger, "_log") as mock_log:
            logger.success("Test success message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], SUCCESS)

    def test_logger_trace_method(self):
        logger = get_logger("test_module")
        logger.setLevel(TRACE)
        with patch.object(logging.Logger, "_log") as mock_log:
            logger.trace("Test trace message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], TRACE)

    def test_stream_handler_writes_error_to_stderr(self):
        stdout = StringIO()
        stderr = StringIO()
        handler = StreamHandler(stdout, stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            "test", logging.ERROR, "test.py", 1, "Error message", (), None
        )
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'tqdm'")
        ):
            handler.emit(record)
            self.assertGreater(len(stderr.getvalue()), 0)

    def test_stream_handler_writes_info_to_stdout(self):
        stdout = StringIO()
        stderr = StringIO()
        handler = StreamHandler(stdout, stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            "test", logging.INFO, "test.py", 1, "Info message", (), None
        )
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'tqdm'")
        ):
            handler.emit(record)
            self.assertGreater(len(stdout.getvalue()), 0)

    def test_githooklib_logger_has_handler(self):
        logger = get_logger("githooklib.test")
        self.assertEqual(len(logger.handlers), 1)
        handler = logger.handlers[0]
        formatter = handler.formatter
        self.assertIsNotNone(formatter)
        self.assertIn("githooklib", formatter._fmt)  # type: ignore[union-attr, arg-type]

    def test_hook_logger_has_own_handler(self):
        logger = get_logger("test_hook", prefix="pre-commit")
        self.assertTrue(logger.propagate)
        self.assertEqual(len(logger.handlers), 1)
        handler = logger.handlers[0]
        formatter = handler.formatter
        self.assertIsNotNone(formatter)
        self.assertIn("pre-commit", formatter._fmt)  # type: ignore[union-attr, arg-type]


if __name__ == "__main__":
    unittest.main()
