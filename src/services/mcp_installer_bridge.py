"""Bridge module between mcp-browser and py-mcp-installer-service.

This module provides a thin integration layer that adapts mcp-browser's
installation needs to the py-mcp-installer-service API.
"""

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

# Optional import - py-mcp-installer may not be installed
try:
    from py_mcp_installer import MCPServerConfig, Platform

    HAS_MCP_INSTALLER = True
except ImportError:
    HAS_MCP_INSTALLER = False
    MCPServerConfig = None  # type: ignore
    Platform = None  # type: ignore

if TYPE_CHECKING:
    from py_mcp_installer import MCPServerConfig, Platform


def detect_installation_type() -> Literal["pipx", "pip", "dev"]:
    """Detect how mcp-browser was installed.

    Returns:
        "pipx" if installed via pipx
        "pip" if installed via pip in a virtual environment
        "dev" if running from development directory
    """
    executable = Path(sys.executable)

    # Check for pipx installation
    if ".local/pipx" in str(executable) or "pipx/venvs" in str(executable):
        return "pipx"

    # Check for development mode
    project_indicators = [".git", "pyproject.toml", "setup.py"]
    current = Path.cwd()
    for _ in range(5):  # Check up to 5 levels up
        if any((current / indicator).exists() for indicator in project_indicators):
            return "dev"
        if current.parent == current:
            break
        current = current.parent

    # Check if in a virtual environment
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        return "pip"

    return "pip"


def get_command_path() -> str:
    """Get the appropriate command path based on installation type.

    Returns:
        Command string to use in MCP configuration
    """
    install_type = detect_installation_type()

    if install_type == "pipx":
        return "mcp-browser"

    elif install_type == "pip":
        which_path = shutil.which("mcp-browser")
        if which_path:
            return which_path
        return "mcp-browser"

    else:  # dev
        # For development, use Python executable
        script_locations = [
            Path.cwd() / "scripts" / "mcp-server.py",
            Path(__file__).parent.parent.parent / "scripts" / "mcp-server.py",
        ]

        for script_path in script_locations:
            if script_path.exists():
                return sys.executable

        return "mcp-browser"


def get_command_args(install_type: Optional[str] = None) -> List[str]:
    """Get command arguments based on installation type.

    Args:
        install_type: The detected installation type (auto-detected if None)

    Returns:
        List of command arguments
    """
    if install_type is None:
        install_type = detect_installation_type()

    if install_type == "dev":
        script_locations = [
            Path.cwd() / "scripts" / "mcp-server.py",
            Path(__file__).parent.parent.parent / "scripts" / "mcp-server.py",
        ]

        for script_path in script_locations:
            if script_path.exists():
                return [str(script_path), "mcp"]

    return ["mcp"]


def get_mcp_browser_config() -> Any:
    """Get the default MCPServerConfig for mcp-browser.

    Returns:
        MCPServerConfig with auto-detected command and args

    Raises:
        ImportError: If py-mcp-installer is not installed
    """
    if not HAS_MCP_INSTALLER:
        raise ImportError(
            "py-mcp-installer is required for this function. "
            "Install it with: pip install py-mcp-installer"
        )

    install_type = detect_installation_type()
    command = get_command_path()
    args = get_command_args(install_type)

    return MCPServerConfig(
        name="mcp-browser",
        command=command,
        args=args,
        env={},
        description="Browser console log capture and control via MCP",
    )


def map_target_to_platforms(target: str) -> List[Any]:
    """Map mcp-browser target names to py-mcp-installer Platforms.

    Args:
        target: Target name (e.g., "claude-code", "claude-desktop", "both")

    Returns:
        List of Platform enums

    Raises:
        ImportError: If py-mcp-installer is not installed
    """
    if not HAS_MCP_INSTALLER:
        raise ImportError(
            "py-mcp-installer is required for this function. "
            "Install it with: pip install py-mcp-installer"
        )

    mapping = {
        "claude-code": [Platform.CLAUDE_CODE],
        "claude-desktop": [Platform.CLAUDE_DESKTOP],
        "both": [Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP],
        # New platforms supported by py-mcp-installer
        "cursor": [Platform.CURSOR],
        "cline": [Platform.CODEX],  # Codex is the internal name for Cline
        "roo-code": [Platform.CODEX],  # Roo-code uses same strategy
        "continue": [Platform.CODEX],  # Continue uses similar strategy
        "zed": [Platform.ANTIGRAVITY],  # Map to available platform
        "windsurf": [Platform.WINDSURF],
        "void": [Platform.CODEX],  # Void uses similar strategy
    }

    return mapping.get(target.lower(), [])


def get_platform_display_name(platform: Any) -> str:
    """Get user-friendly display name for a platform.

    Args:
        platform: Platform enum

    Returns:
        Human-readable platform name

    Raises:
        ImportError: If py-mcp-installer is not installed
    """
    if not HAS_MCP_INSTALLER:
        raise ImportError(
            "py-mcp-installer is required for this function. "
            "Install it with: pip install py-mcp-installer"
        )

    names = {
        Platform.CLAUDE_CODE: "Claude Code",
        Platform.CLAUDE_DESKTOP: "Claude Desktop",
        Platform.CURSOR: "Cursor",
        Platform.CODEX: "Cline/Continue/Roo-Code",
        Platform.WINDSURF: "Windsurf",
        Platform.AUGGIE: "Auggie",
        Platform.GEMINI_CLI: "Gemini CLI",
        Platform.ANTIGRAVITY: "Antigravity",
    }
    return names.get(platform, platform.value)


def get_installation_metadata(install_type: str) -> Dict[str, str]:
    """Get metadata about the current installation.

    Args:
        install_type: The detected installation type

    Returns:
        Dictionary with installation metadata
    """
    command = get_command_path()
    args = get_command_args(install_type)

    return {
        "installation_type": install_type,
        "command": command,
        "args": " ".join(args),
        "python_executable": sys.executable,
    }
