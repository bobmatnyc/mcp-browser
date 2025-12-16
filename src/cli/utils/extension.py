"""Extension management utilities for mcp-browser."""

import json
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple

from . import console


def sync_extension_version(extension_dir: Path, quiet: bool = False) -> bool:
    """Sync extension manifest.json version with package version.

    Args:
        extension_dir: Path to extension directory containing manifest.json
        quiet: If True, suppress console output

    Returns:
        True if version was synced, False if failed or already up-to-date
    """
    from ..._version import __version__

    manifest_path = extension_dir / "manifest.json"
    if not manifest_path.exists():
        return False

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        current_version = manifest.get("version")
        if current_version == __version__:
            return False  # Already up-to-date

        manifest["version"] = __version__
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        if not quiet:
            console.print(
                f"[dim]  Updated manifest.json: {current_version} → {__version__}[/dim]"
            )
        return True
    except Exception as e:
        if not quiet:
            console.print(f"[yellow]  Failed to sync version: {e}[/yellow]")
        return False


def get_extension_version(extension_dir: Path) -> Optional[str]:
    """Get version from extension manifest.json.

    Args:
        extension_dir: Path to extension directory containing manifest.json

    Returns:
        Version string if found, None otherwise
    """
    manifest_path = extension_dir / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        return manifest.get("version")
    except Exception:
        return None


def check_extension_version_sync() -> Tuple[bool, Dict[str, Optional[str]]]:
    """Check if deployed extension versions match package version.

    Returns:
        (is_synced, version_info) where version_info contains:
        - 'package': Package version
        - 'chrome': Chrome extension version (if exists)
        - 'firefox': Firefox extension version (if exists)
        - 'safari': Safari extension version (if exists)
    """
    from ..._version import __version__

    base_dir = Path.cwd() / "mcp-browser-extensions"
    version_info = {
        "package": __version__,
        "chrome": None,
        "firefox": None,
        "safari": None,
    }

    all_synced = True

    for browser in ["chrome", "firefox", "safari"]:
        ext_dir = base_dir / browser
        if ext_dir.exists():
            ext_version = get_extension_version(ext_dir)
            version_info[browser] = ext_version
            if ext_version != __version__:
                all_synced = False

    return all_synced, version_info


def open_chrome_extensions_page() -> bool:
    """Open chrome://extensions page in Chrome browser.

    On macOS, uses AppleScript to open the extensions page.
    On other platforms, returns False (manual action needed).

    Returns:
        True if successfully opened, False otherwise
    """
    if platform.system() != "Darwin":
        return False

    try:
        import subprocess

        # AppleScript to open chrome://extensions in Chrome
        script = """
        tell application "Google Chrome"
            activate
            if (count of windows) = 0 then
                make new window
            end if
            set URL of active tab of window 1 to "chrome://extensions"
        end tell
        """

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return result.returncode == 0

    except Exception:
        return False


def is_chrome_running() -> bool:
    """Check if Chrome is currently running.

    Returns:
        True if Chrome is running, False otherwise
    """
    if platform.system() != "Darwin":
        # On non-macOS, we can't easily detect this
        return False

    try:
        import subprocess

        script = """
        tell application "System Events"
            return (exists process "Google Chrome")
        end tell
        """

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0:
            return result.stdout.strip() == "true"

    except Exception:
        pass

    return False
