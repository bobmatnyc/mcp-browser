"""CLI command modules."""

from .dashboard import dashboard
from .doctor import doctor
from .extension import extension
from .init import init
from .install import install
from .quickstart import quickstart
from .start import start
from .status import status
from .tutorial import tutorial

__all__ = [
    "init",
    "start",
    "status",
    "doctor",
    "dashboard",
    "tutorial",
    "quickstart",
    "install",
    "extension",
]
