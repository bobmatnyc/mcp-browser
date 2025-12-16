"""Extension management utilities for mcp-browser."""

import json
from pathlib import Path
from typing import Optional

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
