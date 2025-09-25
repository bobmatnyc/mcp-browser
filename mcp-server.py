#!/usr/bin/env python3
"""
MCP Server entry point for mcp-browser.
Runs the server in MCP stdio mode for Claude Code integration.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main CLI
from src.cli.main import main

if __name__ == "__main__":
    # Force MCP mode by adding 'mcp' as the command
    sys.argv = [sys.argv[0], 'mcp']
    main()