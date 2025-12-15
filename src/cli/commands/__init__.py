"""CLI command modules."""

from .browser import browser
from .connect import connect
from .demo import demo
from .doctor import doctor
from .extension import extension
from .init import init
from .install import install, uninstall
from .quickstart import quickstart
from .setup import setup
from .start import start
from .status import status
from .stop import stop
from .tutorial import tutorial

__all__ = [
    "init",
    "start",
    "stop",
    "status",
    "doctor",
    "tutorial",
    "quickstart",
    "setup",
    "install",
    "uninstall",
    "extension",
    "browser",
    "connect",
    "demo",
]
