import sys
import unittest
from unittest.mock import patch, MagicMock

from githooklib.__main__ import main
from githooklib.logger import setup_logging
from githooklib.logger import TRACE
from githooklib.git_hook import GitHook
import logging
from tests.base_test_case import BaseTestCase


class TestMain(BaseTestCase):
    def test_setup_logging_with_trace_flag(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "--trace", "other"]
            setup_logging()
            from githooklib.__main__ import logger

            self.assertEqual(logger.level, TRACE)
            self.assertNotIn("--trace", sys.argv)
        finally:
            sys.argv = original_argv

    def test_setup_logging_with_debug_flag(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "--debug", "other"]
            setup_logging()
            from githooklib.__main__ import logger

            self.assertEqual(logger.level, logging.DEBUG)
            self.assertNotIn("--debug", sys.argv)
        finally:
            sys.argv = original_argv

    def test_setup_logging_without_flags(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "other"]
            setup_logging()
            from githooklib.__main__ import logger

            self.assertEqual(logger.level, logging.INFO)
        finally:
            sys.argv = original_argv

    def test_setup_logging_sets_hook_logger_levels(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "--debug", "other"]
            setup_logging()

            class TestHook(GitHook):
                @classmethod
                def get_hook_name(cls):
                    return "test-hook"

                @classmethod
                def get_file_patterns(cls):
                    return None

                def execute(self, context):
                    from githooklib.definitions import HookResult

                    return HookResult(success=True)

            self.assertEqual(TestHook.logger.level, logging.DEBUG)
            for handler in TestHook.logger.handlers:
                self.assertEqual(handler.level, logging.DEBUG)

            sys.argv = ["script", "--trace", "other"]
            setup_logging()

            class TestHook2(GitHook):
                @classmethod
                def get_hook_name(cls):
                    return "test-hook-2"

                @classmethod
                def get_file_patterns(cls):
                    return None

                def execute(self, context):
                    from githooklib.definitions import HookResult

                    return HookResult(success=True)

            self.assertEqual(TestHook2.logger.level, TRACE)
            for handler in TestHook2.logger.handlers:
                self.assertEqual(handler.level, TRACE)
        finally:
            sys.argv = original_argv
            for hook_class in list(GitHook._registered_hooks):
                if hook_class.__name__ in ("TestHook", "TestHook2"):
                    GitHook._registered_hooks.remove(hook_class)

    def test_main_exits_when_project_root_not_found(self):
        original_argv = sys.argv.copy()
        original_exit = sys.exit
        try:
            sys.argv = ["script"]
            exit_called = False
            exit_code = None

            def mock_exit(code: int) -> None:
                nonlocal exit_called, exit_code
                exit_called = True
                exit_code = code
                raise SystemExit(code)

            sys.exit = mock_exit  # type: ignore[assignment]
            with patch(
                "githooklib.__main__.ProjectRootGateway.find_project_root",
                return_value=None,
            ):
                with self.assertRaises(SystemExit):
                    main()
                self.assertTrue(exit_called)
                self.assertEqual(exit_code, 1)
        finally:
            sys.argv = original_argv
            sys.exit = original_exit

    def test_main_calls_fire_with_cli(self):
        original_argv = sys.argv.copy()
        original_exit = sys.exit
        try:
            sys.argv = ["script"]
            with patch(
                "githooklib.__main__.ProjectRootGateway.find_project_root",
                return_value=MagicMock(),
            ):
                with patch(
                    "githooklib.__main__.fire.Fire", return_value=0
                ) as mock_fire:
                    with patch("githooklib.__main__.FireGetResultMock") as mock_mock:
                        with patch("githooklib.__main__.patch") as mock_patch:
                            mock_patch.return_value.__enter__.return_value = None
                            try:
                                main()
                            except SystemExit:
                                pass
                            mock_fire.assert_called()
        finally:
            sys.argv = original_argv
            sys.exit = original_exit

    def test_main_handles_exception(self):
        original_argv = sys.argv.copy()
        original_exit = sys.exit
        try:
            sys.argv = ["script"]
            exit_called = False

            def mock_exit(code: int) -> None:
                nonlocal exit_called
                exit_called = True
                raise SystemExit(code)

            sys.exit = mock_exit  # type: ignore[assignment]
            with patch(
                "githooklib.__main__.ProjectRootGateway.find_project_root",
                return_value=MagicMock(),
            ):
                with patch(
                    "githooklib.__main__.fire.Fire", side_effect=Exception("Error")
                ):
                    with patch("githooklib.__main__.FireGetResultMock"):
                        with patch("githooklib.__main__.patch"):
                            with self.assertRaises(SystemExit):
                                main()
                            self.assertTrue(exit_called)
        finally:
            sys.argv = original_argv
            sys.exit = original_exit

    def test_main_handles_keyboard_interrupt(self):
        original_argv = sys.argv.copy()
        original_exit = sys.exit
        try:
            sys.argv = ["script"]
            exit_called = False

            def mock_exit(code: int) -> None:
                nonlocal exit_called
                exit_called = True
                raise SystemExit(code)

            sys.exit = mock_exit  # type: ignore[assignment]
            with patch(
                "githooklib.__main__.ProjectRootGateway.find_project_root",
                return_value=MagicMock(),
            ):
                with patch(
                    "githooklib.__main__.fire.Fire", side_effect=KeyboardInterrupt()
                ):
                    with patch("githooklib.__main__.FireGetResultMock"):
                        with patch("githooklib.__main__.patch"):
                            with self.assertRaises(SystemExit):
                                main()
                            self.assertTrue(exit_called)
        finally:
            sys.argv = original_argv
            sys.exit = original_exit


if __name__ == "__main__":
    unittest.main()
