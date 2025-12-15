"""CLI module for mcp-browser."""

__all__ = ["main"]


def __getattr__(name: str):
    """Lazy import to avoid circular import issues."""
    if name == "main":
        from .main import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
