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


def read_service_registry() -> dict:
    """
    Read server registry from PID file.

    Returns:
        Dictionary with 'servers' list containing server entries
    """
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                data = json.load(f)
                # Handle legacy format (single server) by converting to new format
                if "pid" in data and "servers" not in data:
                    return {
                        "servers": [
                            {
                                "pid": data["pid"],
                                "port": data["port"],
                                "project_path": data.get("project_path", ""),
                                "started_at": data.get(
                                    "started_at", datetime.now().isoformat()
                                ),
                            }
                        ]
                    }
                return data
        except (json.JSONDecodeError, IOError):
            return {"servers": []}
    return {"servers": []}


def save_server_registry(registry: dict) -> None:
    """Save server registry to PID file."""
    with open(get_pid_file(), "w") as f:
        json.dump(registry, f, indent=2)


def get_project_server(project_path: str) -> Optional[dict]:
    """
    Find server entry for a specific project.

    Args:
        project_path: Absolute path to the project directory

    Returns:
        Server entry dict or None if not found
    """
    # Normalize the project path for consistent comparison
    normalized_path = os.path.normpath(os.path.abspath(project_path))

    registry = read_service_registry()
    for server in registry.get("servers", []):
        # Normalize the stored path as well
        server_path = os.path.normpath(os.path.abspath(server.get("project_path", "")))
        if server_path == normalized_path:
            # Verify process is still running
            if is_process_running(server.get("pid")):
                return server
            # Process died, remove stale entry
            remove_project_server(normalized_path)
    return None


def remove_project_server(project_path: str) -> None:
    """Remove server entry for a specific project."""
    registry = read_service_registry()
    registry["servers"] = [
        s for s in registry.get("servers", []) if s.get("project_path") != project_path
    ]
    save_server_registry(registry)


def add_project_server(pid: int, port: int, project_path: str) -> None:
    """Add or update server entry for a project."""
    registry = read_service_registry()

    # Remove existing entry for this project if any
    registry["servers"] = [
        s for s in registry.get("servers", []) if s.get("project_path") != project_path
    ]

    # Add new entry
    registry["servers"].append(
        {
            "pid": pid,
            "port": port,
            "project_path": project_path,
            "started_at": datetime.now().isoformat(),
        }
    )

    save_server_registry(registry)


def read_service_info() -> Optional[dict]:
    """
    Read service info from PID file (legacy compatibility).

    Deprecated: Use get_project_server() instead for project-aware access.
    """
    registry = read_service_registry()
    servers = registry.get("servers", [])
    if servers:
        # Return first server for backward compatibility
        return servers[0]
    return None


def write_service_info(pid: int, port: int) -> None:
    """
    Write service info to PID file (legacy compatibility).

    Deprecated: Use add_project_server() instead for project-aware access.
    """
    project_path = os.getcwd()
    add_project_server(pid, port, project_path)


def clear_service_info() -> None:
    """
    Remove PID file (legacy compatibility).

    Deprecated: Use remove_project_server() instead for project-aware access.
    """
    project_path = os.getcwd()
    remove_project_server(project_path)


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


def cleanup_stale_servers() -> int:
    """Kill all stale mcp-browser processes and clear registry.

    Scans ports 8851-8899 for any listening processes, checks if they are
    mcp-browser servers, and kills them to ensure clean startup.

    Returns:
        Number of processes killed
    """
    killed = 0

    # Find all processes listening on our port range
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        try:
            # Use lsof to find process on port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                pid_str = result.stdout.strip().split()[0]
                pid = int(pid_str)

                # Check if it's an mcp-browser process
                try:
                    proc_result = subprocess.run(
                        ["ps", "-p", str(pid), "-o", "command="],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if proc_result.returncode == 0:
                        cmd = proc_result.stdout.lower()
                        # Check for mcp-browser package name OR module-based server start
                        is_mcp_browser = "mcp-browser" in cmd or "mcp_browser" in cmd
                        is_module_server = "src.cli.main" in cmd and "start" in cmd
                        if is_mcp_browser or is_module_server:
                            # Kill the process
                            os.kill(pid, 15)  # SIGTERM
                            time.sleep(0.3)
                            if is_process_running(pid):
                                os.kill(pid, 9)  # SIGKILL
                            killed += 1
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    # Skip if we can't check the process
                    pass
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            # Skip if lsof fails or returns invalid data
            pass

    # Clear the registry after cleanup
    save_server_registry({"servers": []})

    return killed


def cleanup_unregistered_servers() -> int:
    """Kill mcp-browser processes that are NOT in the registry.

    This is useful for cleaning up orphaned processes without
    affecting legitimate registered servers.

    Returns:
        Number of processes killed
    """
    killed = 0
    registry = read_service_registry()
    registered_pids = {s.get("pid") for s in registry.get("servers", [])}

    # Find all processes listening on our port range
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                pid_str = result.stdout.strip().split()[0]
                pid = int(pid_str)

                # Skip if this process is registered
                if pid in registered_pids:
                    continue

                # Check if it's an mcp-browser process
                try:
                    proc_result = subprocess.run(
                        ["ps", "-p", str(pid), "-o", "command="],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if proc_result.returncode == 0:
                        cmd = proc_result.stdout.lower()
                        is_mcp_browser = "mcp-browser" in cmd or "mcp_browser" in cmd
                        is_module_server = "src.cli.main" in cmd and "start" in cmd
                        if is_mcp_browser or is_module_server:
                            os.kill(pid, 15)  # SIGTERM
                            time.sleep(0.3)
                            if is_process_running(pid):
                                os.kill(pid, 9)  # SIGKILL
                            killed += 1
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            pass

    return killed


def find_orphaned_project_server(project_path: str) -> Optional[dict]:
    """Find server running for this project but not in registry.

    Scans ports 8851-8899 for mcp-browser processes and checks if they
    were started from the specified project directory.

    Args:
        project_path: Absolute path to the project directory

    Returns:
        Dictionary with 'pid', 'port', 'project_path' or None if not found
    """
    normalized_path = os.path.normpath(os.path.abspath(project_path))

    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        # Check if port is in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            continue  # Port available, no server
        except OSError:
            sock.close()

        # Find PID on this port
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0 or not result.stdout.strip():
                continue

            pid = int(result.stdout.strip().split()[0])

            # Check process command line for mcp-browser
            proc_result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                timeout=2,
            )
            cmd = proc_result.stdout.lower()

            # Must be mcp-browser process
            if "mcp-browser" not in cmd and "mcp_browser" not in cmd:
                continue

            # Check if process cwd matches project (macOS)
            cwd_result = subprocess.run(
                ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            # Parse cwd from lsof output (format: "n/path/to/dir")
            for line in cwd_result.stdout.split("\n"):
                if line.startswith("n/"):
                    process_cwd = line[1:]  # Remove 'n' prefix
                    if os.path.normpath(process_cwd) == normalized_path:
                        return {
                            "pid": pid,
                            "port": port,
                            "project_path": project_path,
                        }

        except (subprocess.TimeoutExpired, ValueError, OSError):
            continue

    return None


def get_server_status(
    project_path: Optional[str] = None,
) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Check if server is running for the specified or current project.

    Args:
        project_path: Project directory to check (default: current directory)

    Returns:
        (is_running, pid, port) tuple
    """
    if project_path is None:
        project_path = os.getcwd()

    # Normalize path for consistent comparison
    project_path = os.path.normpath(os.path.abspath(project_path))

    server = get_project_server(project_path)
    if server:
        return True, server.get("pid"), server.get("port")
    return False, None, None


def start_daemon(
    port: Optional[int] = None,
) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Start server as background daemon for the current project.

    If a server is already running for this project and no specific port
    is requested, the existing server will be reused. Otherwise, the old
    server will be stopped and restarted on the requested port.

    Args:
        port: Specific port to use, or None to auto-select/reuse existing

    Returns:
        (success, pid, port) tuple
    """
    project_path = os.getcwd()

    # Check if server already exists for this project FIRST
    existing_server = get_project_server(project_path)

    if existing_server:
        # Server already running for this project
        existing_pid = existing_server.get("pid")
        existing_port = existing_server.get("port")

        # If it's running and we didn't request a specific port, just return it
        if port is None and is_process_running(existing_pid):
            return True, existing_pid, existing_port

        # If specific port requested or process is dead, clean up THIS project's server only
        try:
            if is_process_running(existing_pid):
                os.kill(existing_pid, 15)  # SIGTERM
                time.sleep(0.5)
                if is_process_running(existing_pid):
                    os.kill(existing_pid, 9)  # SIGKILL
        except (OSError, ProcessLookupError):
            pass

        # Reuse the existing port if not specified
        if port is None:
            port = existing_port

        # Remove old registry entry
        remove_project_server(project_path)
    else:
        # Check for orphaned server not in registry
        orphaned = find_orphaned_project_server(project_path)
        if orphaned:
            # Add to registry and reuse
            add_project_server(
                orphaned["pid"], orphaned["port"], orphaned["project_path"]
            )
            return True, orphaned["pid"], orphaned["port"]

    # Find available port if not specified
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
            add_project_server(process.pid, port, project_path)
            return True, process.pid, port
        else:
            return False, None, None

    except Exception:
        return False, None, None


def stop_daemon() -> bool:
    """Stop the running daemon for the current project."""
    project_path = os.getcwd()
    server = get_project_server(project_path)

    if not server:
        return True

    pid = server.get("pid")
    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(0.5)
        if is_process_running(pid):
            os.kill(pid, 9)  # SIGKILL
        remove_project_server(project_path)
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
