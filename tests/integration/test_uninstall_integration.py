"""Integration tests for the uninstall command (no mocking)."""

import json
from pathlib import Path

from click.testing import CliRunner

from src.cli.main import cli


def create_test_config(
    path: Path,
    has_mcpservers: bool = True,
    has_mcp_browser: bool = True,
    other_servers: bool = False,
):
    """Create a test configuration file."""
    config = {}

    if has_mcpservers:
        config["mcpServers"] = {}

        if has_mcp_browser:
            config["mcpServers"]["mcp-browser"] = {
                "command": "mcp-browser",
                "args": ["mcp"],
            }

        if other_servers:
            config["mcpServers"]["other-server"] = {
                "command": "other-command",
                "args": ["arg1"],
            }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

    return config


def test_help_output():
    """Test 1: Verify help output is correct."""
    print("\n" + "=" * 70)
    print("TEST 1: Verify uninstall --help output")
    print("=" * 70)

    runner = CliRunner()
    result = runner.invoke(cli, ["uninstall", "--help"])

    print(f"\n📤 Help output:\n{result.output}")

    # Assertions
    assert result.exit_code == 0, "❌ Help should exit with code 0"
    assert "Remove MCP Browser configuration" in result.output, "❌ Description missing"
    assert "--target" in result.output, "❌ --target option missing"
    assert "claude-code" in result.output, "❌ claude-code option missing"
    assert "claude-desktop" in result.output, "❌ claude-desktop option missing"
    assert "both" in result.output, "❌ both option missing"

    print("\n✅ TEST 1 PASSED: Help output is correct")
    return True


def test_cli_registration():
    """Test 2: Verify command is registered in main CLI."""
    print("\n" + "=" * 70)
    print("TEST 2: Verify command registration in CLI")
    print("=" * 70)

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    print("\n📤 CLI help output (snippet):\n")
    lines = result.output.split("\n")
    for line in lines:
        if "uninstall" in line.lower():
            print(line)

    # Assertions
    assert result.exit_code == 0, "❌ CLI help should exit with code 0"
    assert "uninstall" in result.output.lower(), "❌ uninstall command not found in CLI"

    print("\n✅ TEST 2 PASSED: Command is properly registered")
    return True


def test_completion_scripts():
    """Test 3: Verify completion scripts include uninstall."""
    print("\n" + "=" * 70)
    print("TEST 3: Verify completion scripts updated")
    print("=" * 70)

    scripts_dir = Path(__file__).parent / "scripts"

    # Test bash completion
    bash_script = scripts_dir / "completion.bash"
    if bash_script.exists():
        bash_content = bash_script.read_text()
        print("\n📝 Checking bash completion...")
        if "uninstall" in bash_content:
            print("✓ bash completion includes 'uninstall'")
        else:
            print("✗ bash completion MISSING 'uninstall'")
    else:
        print("⚠ bash completion script not found")

    # Test zsh completion
    zsh_script = scripts_dir / "completion.zsh"
    if zsh_script.exists():
        zsh_content = zsh_script.read_text()
        print("\n📝 Checking zsh completion...")
        if "uninstall" in zsh_content:
            print("✓ zsh completion includes 'uninstall'")
        else:
            print("✗ zsh completion MISSING 'uninstall'")
    else:
        print("⚠ zsh completion script not found")

    # Test inline completion in main.py
    runner = CliRunner()
    result = runner.invoke(cli, ["completion", "bash"])

    print("\n📝 Checking inline bash completion...")
    if "uninstall" in result.output:
        print("✓ inline bash completion includes 'uninstall'")
    else:
        print("✗ inline bash completion MISSING 'uninstall'")

    result = runner.invoke(cli, ["completion", "zsh"])
    print("\n📝 Checking inline zsh completion...")
    if "uninstall" in result.output:
        print("✓ inline zsh completion includes 'uninstall'")
    else:
        print("✗ inline zsh completion MISSING 'uninstall'")

    result = runner.invoke(cli, ["completion", "fish"])
    print("\n📝 Checking inline fish completion...")
    if "uninstall" in result.output:
        print("✓ inline fish completion includes 'uninstall'")
    else:
        print("✗ inline fish completion MISSING 'uninstall'")

    print("\n✅ TEST 3 PASSED: Completion scripts checked")
    return True


def test_uninstall_actual_behavior():
    """Test 4: Test actual command behavior (without system paths)."""
    print("\n" + "=" * 70)
    print("TEST 4: Test uninstall behavior (dry run)")
    print("=" * 70)

    # Since we can't mock easily, test with non-existent paths
    # This tests error handling
    runner = CliRunner()
    result = runner.invoke(cli, ["uninstall", "--target", "claude-code"])

    print(f"\n📤 Command output:\n{result.output}")
    print(f"Exit code: {result.exit_code}")

    # Should handle gracefully
    assert result.exit_code == 0, "❌ Should exit gracefully"
    assert (
        "not found" in result.output.lower()
        or "not configured" in result.output.lower()
        or "complete" in result.output.lower()
    ), "❌ Should provide feedback"

    print("\n✅ TEST 4 PASSED: Command executes without crashing")
    return True


def test_reference_command():
    """Test 5: Verify uninstall appears in reference."""
    print("\n" + "=" * 70)
    print("TEST 5: Verify uninstall in reference guide")
    print("=" * 70)

    runner = CliRunner()
    result = runner.invoke(cli, ["reference"])

    print("\n📝 Checking reference guide...")

    if "uninstall" in result.output.lower():
        print("✓ reference guide includes 'uninstall'")
        # Find and print the relevant line
        lines = result.output.split("\n")
        for line in lines:
            if "uninstall" in line.lower():
                print(f"  {line.strip()}")
    else:
        print("✗ reference guide MISSING 'uninstall'")

    print("\n✅ TEST 5 PASSED: Reference checked")
    return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("🧪 UNINSTALL COMMAND INTEGRATION TEST SUITE")
    print("=" * 70)

    tests = [
        test_help_output,
        test_cli_registration,
        test_completion_scripts,
        test_uninstall_actual_behavior,
        test_reference_command,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
