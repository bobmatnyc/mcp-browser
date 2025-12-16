#!/usr/bin/env python3
"""Test daemon server reuse behavior after fix."""

from unittest.mock import MagicMock, patch

import pytest

from src.cli.utils.daemon import start_daemon


@pytest.mark.asyncio
async def test_start_daemon_reuses_existing_server():
    """Test that start_daemon reuses existing server instead of killing it."""

    # Mock project path
    project_path = "/fake/project"

    # Mock existing server info
    existing_pid = 12345
    existing_port = 8851
    existing_server = {
        "pid": existing_pid,
        "port": existing_port,
        "project_path": project_path,
        "started_at": "2025-12-15T12:00:00",
    }

    with (
        patch("src.cli.utils.daemon.os.getcwd", return_value=project_path),
        patch("src.cli.utils.daemon.get_project_server", return_value=existing_server),
        patch(
            "src.cli.utils.daemon.is_process_running", return_value=True
        ) as mock_is_running,
        patch("src.cli.utils.daemon.os.kill") as mock_kill,
    ):
        # Call start_daemon without specific port (should reuse existing)
        success, pid, port = start_daemon(port=None)

        # Should return existing server info
        assert success is True
        assert pid == existing_pid
        assert port == existing_port

        # Should NOT kill the process
        mock_kill.assert_not_called()

        # Should check if process is running
        mock_is_running.assert_called_with(existing_pid)


@pytest.mark.asyncio
async def test_start_daemon_restarts_when_port_requested():
    """Test that start_daemon restarts server when specific port requested."""

    project_path = "/fake/project"
    existing_pid = 12345
    existing_port = 8851
    requested_port = 8852  # Different port

    existing_server = {
        "pid": existing_pid,
        "port": existing_port,
        "project_path": project_path,
        "started_at": "2025-12-15T12:00:00",
    }

    with (
        patch("src.cli.utils.daemon.os.getcwd", return_value=project_path),
        patch("src.cli.utils.daemon.get_project_server", return_value=existing_server),
        patch("src.cli.utils.daemon.is_process_running", return_value=True),
        patch("src.cli.utils.daemon.os.kill") as mock_kill,
        patch("src.cli.utils.daemon.remove_project_server"),
        patch("src.cli.utils.daemon.subprocess.Popen") as mock_popen,
        patch("src.cli.utils.daemon.add_project_server"),
        patch(
            "src.cli.utils.daemon.shutil.which",
            return_value="/usr/local/bin/mcp-browser",
        ),
        patch("src.cli.utils.daemon.time.sleep"),
    ):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 99999
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        # Call start_daemon WITH specific port (should restart)
        success, pid, port = start_daemon(port=requested_port)

        # Should kill the old process
        assert mock_kill.called
        assert mock_kill.call_args_list[0][0][0] == existing_pid

        # Should start new process
        assert mock_popen.called


@pytest.mark.asyncio
async def test_start_daemon_no_cleanup_stale_servers_call():
    """Test that start_daemon does NOT call cleanup_stale_servers."""

    project_path = "/fake/project"

    with (
        patch("src.cli.utils.daemon.os.getcwd", return_value=project_path),
        patch("src.cli.utils.daemon.get_project_server", return_value=None),
        patch("src.cli.utils.daemon.find_available_port", return_value=8851),
        patch("src.cli.utils.daemon.subprocess.Popen") as mock_popen,
        patch("src.cli.utils.daemon.add_project_server"),
        patch(
            "src.cli.utils.daemon.shutil.which",
            return_value="/usr/local/bin/mcp-browser",
        ),
        patch("src.cli.utils.daemon.time.sleep"),
        patch("src.cli.utils.daemon.cleanup_stale_servers") as mock_cleanup,
    ):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 99999
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Call start_daemon
        start_daemon(port=None)

        # CRITICAL: cleanup_stale_servers should NOT be called
        mock_cleanup.assert_not_called()
