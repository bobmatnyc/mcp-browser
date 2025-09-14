"""Setup script for browserpymcp package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="browserpymcp",
    version="1.0.0",
    author="BrowserPyMCP Team",
    author_email="support@browserpymcp.dev",
    description="MCP server for browser console log capture and control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/browserpymcp/mcp-browser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.1.0",
        "websockets>=11.0,<13.0",
        "playwright>=1.40.0",
        "aiofiles>=23.0.0,<24.0",
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
            "browserpymcp=src.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.html", "*.js", "*.css", "*.png"],
    },
    zip_safe=False,
)