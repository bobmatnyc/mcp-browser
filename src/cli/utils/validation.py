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

    # Playwright browsers
    playwright_ok = False
    try:
        playwright_ok = True
    except Exception:
        pass
    checks.append(("Playwright", playwright_ok, "For screenshots"))

    # Port availability
    port_available = False
    for port in range(8875, 8896):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                port_available = True
                break
            except Exception:
                pass
    checks.append(("Port availability", port_available, "Ports 8875-8895"))

    return checks


async def check_installation_status() -> Dict[str, Any]:
    """Check the installation status of mcp-browser."""
    status = {
        "package_installed": True,  # We're running, so it's installed
        "config_exists": CONFIG_FILE.exists(),
        "extension_initialized": False,
        "data_dir_exists": DATA_DIR.exists(),
        "logs_dir_exists": LOG_DIR.exists(),
        "server_running": False,
        "extension_installed": False,
    }

    # Check for project-local extension
    local_ext = Path.cwd() / ".mcp-browser" / "extension"
    status["extension_initialized"] = local_ext.exists()

    # Check if server is running (by checking port)
    for port in range(8875, 8896):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(("localhost", port)) == 0:
                status["server_running"] = True
                status["server_port"] = port
                break

    return status
