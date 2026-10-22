"""Regression tests for daemon startup without opening windows or processes."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROJECT_DIR = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("crosshair_gui", PROJECT_DIR / "crosshair-gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


class DaemonStartupTests(unittest.TestCase):
    def assert_daemon_startup(self, config_path, socket_path):
        # Only startup needs exercising; constructing a GTK window would
        # also load settings and schedule real daemon/status operations.
        settings = SimpleNamespace(
            config_path=config_path,
            socket_path=socket_path,
            _set_status_text=Mock(),
            _after_start_check=Mock(),
        )

        with (
            patch.object(gui.subprocess, "Popen") as launch,
            patch.object(gui.GLib, "timeout_add") as timeout_add,
        ):
            gui.CrosshairSettingsWindow._start_overlay(settings)

        launch.assert_called_once_with(
            [
                sys.executable,
                str(PROJECT_DIR / "crosshaird.py"),
                "--config", str(config_path),
                "--socket", str(socket_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        settings._set_status_text.assert_called_once_with("Starting…")
        timeout_add.assert_called_once_with(1200, settings._after_start_check)

    def test_default_paths(self):
        self.assert_daemon_startup(gui.DEFAULT_CONFIG_PATH, gui.DEFAULT_SOCKET_PATH)

    def test_custom_config_path(self):
        self.assert_daemon_startup(
            Path("/tmp/crosshair-test/config.toml"), gui.DEFAULT_SOCKET_PATH
        )

    def test_custom_socket_path(self):
        self.assert_daemon_startup(
            gui.DEFAULT_CONFIG_PATH, Path("/tmp/crosshair-test/control.sock")
        )

    def test_custom_config_and_socket_paths(self):
        self.assert_daemon_startup(
            Path("/tmp/crosshair-test/config.toml"),
            Path("/tmp/crosshair-test/control.sock"),
        )

    def test_paths_with_spaces(self):
        self.assert_daemon_startup(
            Path("profiles/custom crosshair.toml"),
            Path("/tmp/crosshair test/control socket.sock"),
        )


if __name__ == "__main__":
    unittest.main()
