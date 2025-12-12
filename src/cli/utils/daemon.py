"""Daemon management for mcp-browser server."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Port range for server
PORT_RANGE_START = 8851
PORT_RANGE_END = 8899


def get_config_dir() -> Path:
    """Get the mcp-browser config directory."""
    config_dir = Path.home() / ".mcp-browser"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_pid_file() -> Path:
    """Get path to PID file."""
    return get_config_dir() / "server.pid"


def read_service_info() -> Optional[dict]:
    """Read service info from PID file."""
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def write_service_info(pid: int, port: int) -> None:
    """Write service info to PID file."""
    info = {"pid": pid, "port": port, "started_at": datetime.now().isoformat()}
    with open(get_pid_file(), "w") as f:
        json.dump(info, f)


def clear_service_info() -> None:
    """Remove PID file."""
    pid_file = get_pid_file()
    if pid_file.exists():
        pid_file.unlink()


def is_process_running(pid: int) -> bool:
    """Check if process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def is_port_available(port: int) -> bool:
    """Check if port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", port))
            return True
    except OSError:
        return False


def find_available_port() -> Optional[int]:
    """Find first available port in range."""
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        if is_port_available(port):
            return port
    return None


def get_server_status() -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Check if server is running.

    Returns:
        (is_running, pid, port) tuple
    """
    info = read_service_info()
    if info:
        pid = info.get("pid")
        port = info.get("port")
        if pid and is_process_running(pid):
            return True, pid, port
        # Stale PID file
        clear_service_info()
    return False, None, None


def start_daemon(
    port: Optional[int] = None,
) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Start server as background daemon.

    Args:
        port: Specific port to use, or None to auto-select

    Returns:
        (success, pid, port) tuple
    """
    # Check if already running
    is_running, existing_pid, existing_port = get_server_status()
    if is_running:
        return True, existing_pid, existing_port

    # Find available port
    if port is None:
        port = find_available_port()
        if port is None:
            return False, None, None

    # Start server as daemon
    # Use the CLI executable instead of python -m
    mcp_browser_path = shutil.which("mcp-browser")
    if not mcp_browser_path:
        # Fallback: try relative to Python executable
        mcp_browser_path = os.path.join(os.path.dirname(sys.executable), "mcp-browser")
        if not os.path.exists(mcp_browser_path):
            return False, None, None

    cmd = [mcp_browser_path, "start", "--port", str(port), "--daemon"]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait briefly for startup
        time.sleep(1)

        # Verify it started
        if process.poll() is None:
            write_service_info(process.pid, port)
            return True, process.pid, port
        else:
            return False, None, None

    except Exception:
        return False, None, None


def stop_daemon() -> bool:
    """Stop the running daemon."""
    is_running, pid, _ = get_server_status()
    if not is_running:
        return True

    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(0.5)
        if is_process_running(pid):
            os.kill(pid, 9)  # SIGKILL
        clear_service_info()
        return True
    except Exception:
        return False


def ensure_server_running() -> Tuple[bool, Optional[int]]:
    """
    Ensure server is running, starting it if necessary.

    Returns:
        (success, port) tuple
    """
    is_running, _, port = get_server_status()
    if is_running:
        return True, port

    success, _, port = start_daemon()
    return success, port
