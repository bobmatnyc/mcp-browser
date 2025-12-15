"""Validation utilities for system requirements and installation."""

import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Default paths
HOME_DIR = Path.home() / ".mcp-browser"
CONFIG_FILE = HOME_DIR / "config" / "settings.json"
LOG_DIR = HOME_DIR / "logs"
DATA_DIR = HOME_DIR / "data"


def is_first_run() -> bool:
    """Check if this is the first time running mcp-browser."""
    return not HOME_DIR.exists() or not CONFIG_FILE.exists()


async def check_system_requirements() -> List[Tuple[str, bool, str]]:
    """Check system requirements and return status."""
    checks = []

    # Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(
        (
            "Python 3.10+",
            py_ok,
            f"Python {py_version.major}.{py_version.minor}.{py_version.micro}",
        )
    )

    # Chrome/Chromium
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium",  # Linux Chromium
    ]
    chrome_found = (
        any(Path(p).exists() for p in chrome_paths)
        or shutil.which("chrome")
        or shutil.which("chromium")
    )
    checks.append(("Chrome/Chromium", chrome_found, "Required for extension"))

    # Node.js (optional but useful)
    node_found = shutil.which("node") is not None
    node_version = "Not installed"
    if node_found:
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True
            )
            node_version = result.stdout.strip()
        except Exception:
            pass
    checks.append(("Node.js (optional)", node_found, node_version))

    # Port availability
    from .daemon import PORT_RANGE_END, PORT_RANGE_START

    port_available = False
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                port_available = True
                break
            except Exception:
                pass
    checks.append(
        (
            "Port availability",
            port_available,
            f"Ports {PORT_RANGE_START}-{PORT_RANGE_END}",
        )
    )

    return checks


async def check_installation_status() -> Dict[str, Any]:
    """Check the installation status of mcp-browser."""
    from .daemon import get_server_status

    status = {
        "package_installed": True,  # We're running, so it's installed
        "config_exists": CONFIG_FILE.exists(),
        "extension_initialized": False,
        "data_dir_exists": DATA_DIR.exists(),
        "logs_dir_exists": LOG_DIR.exists(),
        "server_running": False,
        "extension_installed": False,
    }

    # Check for project-local extension (visible directory, no dot prefix)
    local_ext = Path.cwd() / "mcp-browser-extensions" / "chrome"
    status["extension_initialized"] = local_ext.exists()

    # Check if server is running using daemon module's status function
    is_running, pid, port = get_server_status()
    status["server_running"] = is_running
    if port:
        status["server_port"] = port

    return status
