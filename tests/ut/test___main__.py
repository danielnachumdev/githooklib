import sys
import unittest
from unittest.mock import patch, MagicMock

from githooklib.__main__ import main, _setup_logging
from githooklib.logger import TRACE
import logging
from tests.base_test_case import BaseTestCase


class TestMain(BaseTestCase):
    def test_setup_logging_with_trace_flag(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "--trace", "other"]
            _setup_logging()
            self.assertEqual(logging.getLogger().level, TRACE)
            self.assertNotIn("--trace", sys.argv)
        finally:
            sys.argv = original_argv

    def test_setup_logging_with_debug_flag(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "--debug", "other"]
            _setup_logging()
            self.assertEqual(logging.getLogger().level, logging.DEBUG)
            self.assertNotIn("--debug", sys.argv)
        finally:
            sys.argv = original_argv

    def test_setup_logging_without_flags(self):
        original_argv = sys.argv.copy()
        try:
            sys.argv = ["script", "other"]
            _setup_logging()
            self.assertEqual(logging.getLogger().level, logging.INFO)
        finally:
            sys.argv = original_argv

    def test_main_exits_when_project_root_not_found(self):
        original_argv = sys.argv.copy()
        original_exit = sys.exit
        try:
            sys.argv = ["script"]
            exit_called = False
            exit_code = None

            def mock_exit(code):
                nonlocal exit_called, exit_code
                exit_called = True
                exit_code = code
                raise SystemExit(code)

            sys.exit = mock_exit
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

            def mock_exit(code):
                nonlocal exit_called
                exit_called = True
                raise SystemExit(code)

            sys.exit = mock_exit
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

            def mock_exit(code):
                nonlocal exit_called
                exit_called = True
                raise SystemExit(code)

            sys.exit = mock_exit
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
