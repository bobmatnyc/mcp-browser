"""Tutorial command implementation."""

import click
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ..utils import console

# Tutorial lessons data
LESSONS = [
    {
        "title": "Lesson 1: Understanding MCP Browser",
        "content": """
MCP Browser creates a bridge between your web browser and Claude Code.

Key concepts:
• **WebSocket Server**: Listens for browser connections (ports 8875-8895)
• **Chrome Extension**: Captures console logs from any website
• **MCP Tools**: Exposes browser control to Claude Code
• **Storage**: Persists logs with automatic rotation

The flow:
1. Chrome extension connects to local WebSocket server
2. Extension captures all console.log messages
3. Server stores messages and exposes them via MCP
4. Claude Code can query logs and control browser
""",
    },
    {
        "title": "Lesson 2: Installation",
        "content": """
Let's verify your installation:

1. **Check Python version** (needs 3.10+):
   $ python --version

2. **Install mcp-browser**:
   $ pip install mcp-browser

3. **Initialize extension**:
   $ mcp-browser init --project  # For current project
   $ mcp-browser init --global   # For system-wide

4. **Verify installation**:
   $ mcp-browser doctor
""",
    },
    {
        "title": "Lesson 3: Starting the Server",
        "content": """
Start the MCP Browser server:

$ mcp-browser start

This will:
• Start WebSocket server (auto-selects port 8875-8895)
• Launch dashboard at http://localhost:8080
• Begin listening for browser connections

Options:
• --no-dashboard: Skip dashboard
• --port 8880: Use specific WebSocket port
• --debug: Enable debug logging
""",
    },
    {
        "title": "Lesson 4: Installing Chrome Extension",
        "content": """
Install the Chrome extension:

1. Start the server: `mcp-browser start`
2. Open dashboard: http://localhost:8080
3. Click "Install Extension" button
4. Or manually:
   a. Open Chrome Extensions (chrome://extensions)
   b. Enable "Developer mode"
   c. Click "Load unpacked"
   d. Select .mcp-browser/extension folder

5. Verify connection in extension popup (puzzle icon)
""",
    },
    {
        "title": "Lesson 5: Capturing Console Logs",
        "content": """
Once connected, the extension captures all console output:

1. Open any website
2. Open DevTools Console (F12)
3. Type: console.log('Hello from MCP!')
4. Check dashboard to see captured message

Captured data includes:
• Message content
• Timestamp
• URL and title
• Log level (log, warn, error)
• Stack traces for errors
""",
    },
    {
        "title": "Lesson 6: Using with Claude Code",
        "content": """
Configure Claude Code to use MCP Browser:

1. **For Claude Desktop**, add to config:
   {
     "mcpServers": {
       "mcp-browser": {
         "command": "mcp-browser",
         "args": ["mcp"]
       }
     }
   }

2. **Available MCP tools**:
   • browser_navigate: Navigate to URL
   • browser_query_logs: Search console logs
   • browser_screenshot: Capture screenshots

3. **Example usage in Claude**:
   "Navigate to example.com and show me any console errors"
""",
    },
    {
        "title": "Lesson 7: Troubleshooting",
        "content": """
Common issues and solutions:

**Extension not connecting:**
• Check server is running: `mcp-browser status`
• Verify port in extension popup matches server
• Try different port: `mcp-browser start --port 8880`

**No logs appearing:**
• Refresh the webpage
• Check extension is enabled in Chrome
• Verify connection status in extension popup

**Server won't start:**
• Port in use: Server auto-tries next port
• Permission issues: Check directory permissions
• Run `mcp-browser doctor --fix`
""",
    },
]


@click.command()
@click.pass_context
def tutorial(ctx):
    """📚 Interactive tutorial for using MCP Browser.

    \b
    Step-by-step guide that covers:
      1. Installation and setup
      2. Starting the server
      3. Installing the Chrome extension
      4. Capturing console logs
      5. Using MCP tools with Claude Code
      6. Troubleshooting common issues

    Perfect for new users who want to learn by doing!
    """
    console.print(
        Panel.fit(
            "[bold magenta]📚 MCP Browser Interactive Tutorial[/bold magenta]\n\n"
            "This tutorial will guide you through using MCP Browser step by step.",
            title="Tutorial",
            border_style="magenta",
        )
    )

    current_lesson = 0

    while current_lesson < len(LESSONS):
        lesson = LESSONS[current_lesson]

        console.clear()
        console.print(
            Panel(
                Markdown(lesson["content"]),
                title=f"[bold]{lesson['title']}[/bold]",
                border_style="blue",
                padding=(1, 2),
            )
        )

        console.print("\n" + "─" * 50)

        if current_lesson < len(LESSONS) - 1:
            choice = Prompt.ask(
                "\n[bold]Continue?[/bold]",
                choices=["next", "previous", "quit", "practice"],
                default="next",
            )
        else:
            choice = Prompt.ask(
                "\n[bold]Tutorial complete![/bold]",
                choices=["previous", "quit", "restart"],
                default="quit",
            )

        if choice == "next":
            current_lesson += 1
        elif choice == "previous":
            current_lesson = max(0, current_lesson - 1)
        elif choice == "restart":
            current_lesson = 0
        elif choice == "practice":
            console.print("\n[cyan]Opening a new terminal for practice...[/cyan]")
            console.print("[dim]Type 'exit' to return to the tutorial[/dim]")
            input("\nPress Enter to continue...")
        else:  # quit
            break

    console.print("\n[green]Thanks for completing the tutorial![/green]")
    console.print("\nNext steps:")
    console.print("  • Run [cyan]mcp-browser quickstart[/cyan] for setup")
    console.print("  • Run [cyan]mcp-browser start[/cyan] to begin")
    console.print(
        "  • Visit [link=https://docs.mcp-browser.dev]documentation[/link] for more info"
    )
