import logging
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from githooklib.logger import (
    get_logger,
    Logger,
    StreamRouter,
    DisplayNameFormatter,
    GithooklibFilter,
    TRACE,
    SUCCESS,
)
from tests.base_test_case import BaseTestCase


class TestLogger(BaseTestCase):
    def test_get_logger_returns_logger_instance(self):
        logger = get_logger("test_module")
        self.assertIsInstance(logger, Logger)

    def test_get_logger_with_display_name(self):
        logger = get_logger("test_module", "custom_name")
        self.assertEqual(logger.display_name, "custom_name")

    def test_logger_set_level_updates_root_logger(self):
        logger = get_logger("test_module")
        logger.setLevel(logging.DEBUG)
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)

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

    def test_stream_router_writes_error_to_stderr(self):
        stdout = StringIO()
        stderr = StringIO()
        router = StreamRouter(stdout, stderr)
        router.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            "test", logging.ERROR, "test.py", 1, "Error message", (), None
        )
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'tqdm'")
        ):
            router.emit(record)
            self.assertGreater(len(stderr.getvalue()), 0)

    def test_stream_router_writes_info_to_stdout(self):
        stdout = StringIO()
        stderr = StringIO()
        router = StreamRouter(stdout, stderr)
        router.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            "test", logging.INFO, "test.py", 1, "Info message", (), None
        )
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'tqdm'")
        ):
            router.emit(record)
            self.assertGreater(len(stdout.getvalue()), 0)

    def test_display_name_formatter_formats_githooklib_records(self):
        formatter = DisplayNameFormatter()
        record = logging.LogRecord(
            "githooklib.test",
            logging.INFO,
            "test.py",
            1,
            "Test message",
            (),
            None,
        )
        record.display_name = "githooklib"
        result = formatter.format(record)
        self.assertIn("githooklib", result)
        self.assertIn("Test message", result)

    def test_display_name_formatter_formats_non_githooklib_records(self):
        formatter = DisplayNameFormatter()
        record = logging.LogRecord(
            "other.module", logging.INFO, "test.py", 1, "Test message", (), None
        )
        result = formatter.format(record)
        self.assertIn("Test message", result)

    def test_githooklib_filter_filters_githooklib_logs(self):
        filter_obj = GithooklibFilter()
        record = logging.LogRecord(
            "githooklib.test",
            logging.INFO,
            "test.py",
            1,
            "Test message",
            (),
            None,
        )
        result = filter_obj.filter(record)
        self.assertTrue(result)

    def test_githooklib_filter_filters_hook_files(self):
        filter_obj = GithooklibFilter()
        record = logging.LogRecord(
            "other.module",
            logging.INFO,
            "githooks/pre_commit.py",
            1,
            "Test message",
            (),
            None,
        )
        result = filter_obj.filter(record)
        self.assertTrue(result)

    def test_githooklib_filter_filters_hook_files_by_name(self):
        filter_obj = GithooklibFilter()
        record = logging.LogRecord(
            "other.module",
            logging.INFO,
            "test_hook.py",
            1,
            "Test message",
            (),
            None,
        )
        result = filter_obj.filter(record)
        self.assertTrue(result)

    def test_githooklib_filter_rejects_other_logs(self):
        filter_obj = GithooklibFilter()
        record = logging.LogRecord(
            "other.module",
            logging.INFO,
            "other.py",
            1,
            "Test message",
            (),
            None,
        )
        result = filter_obj.filter(record)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
