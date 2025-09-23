"""Setup script for mcp-browser package."""

from setuptools import setup, find_packages
from pathlib import Path
import sys
import os

# Add src to path to import _version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from _version import __version__, __author__, __author_email__, __description__

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="mcp-browser",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/browserpymcp/mcp-browser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=0.1.0",
        "websockets>=11.0",
        "playwright>=1.40.0",
        "aiofiles>=23.0.0",
        "aiohttp>=3.9.0",
        "click>=8.1.0",
        "rich>=13.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mcp-browser=mcp_browser.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.html", "*.js", "*.css", "*.png"],
    },
    zip_safe=False,
)