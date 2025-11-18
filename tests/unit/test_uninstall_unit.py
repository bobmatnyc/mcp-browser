"""Unit tests for uninstall helper functions."""

import json
import tempfile
from pathlib import Path

from src.cli.commands.install import (
    load_or_create_config,
    remove_from_mcp_config,
    save_config,
)


def test_load_existing_config():
    """Test 1: Load an existing valid config."""
    print("\n" + "=" * 70)
    print("TEST 1: Load existing valid config")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"

        # Create a valid config
        test_config = {"mcpServers": {"test": {"command": "test"}}}
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        # Load it
        loaded = load_or_create_config(config_path)

        print(f"\n📝 Original: {test_config}")
        print(f"📝 Loaded: {loaded}")

        assert loaded == test_config, "❌ Config should match"

        print("\n✅ TEST 1 PASSED: Loaded valid config correctly")
        return True


def test_load_nonexistent_config():
    """Test 2: Load a config that doesn't exist."""
    print("\n" + "=" * 70)
    print("TEST 2: Load non-existent config")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.json"

        # Load non-existent file
        loaded = load_or_create_config(config_path)

        print(f"\n📝 Loaded: {loaded}")

        assert loaded == {}, "❌ Should return empty dict"

        print("\n✅ TEST 2 PASSED: Returns empty dict for non-existent file")
        return True


def test_load_invalid_json():
    """Test 3: Load a config with invalid JSON."""
    print("\n" + "=" * 70)
    print("TEST 3: Load config with invalid JSON")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "invalid.json"

        # Create invalid JSON
        with open(config_path, "w") as f:
            f.write("{invalid json here}")

        # Load it
        loaded = load_or_create_config(config_path)

        print(f"\n📝 Loaded: {loaded}")

        assert loaded == {}, "❌ Should return empty dict for invalid JSON"

        print("\n✅ TEST 3 PASSED: Gracefully handles invalid JSON")
        return True


def test_save_config():
    """Test 4: Save a config file."""
    print("\n" + "=" * 70)
    print("TEST 4: Save config file")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "subdir" / "config.json"

        test_config = {"mcpServers": {"test": {"command": "test"}}}

        # Save it
        success = save_config(config_path, test_config)

        print(f"\n📝 Save success: {success}")
        print(f"📝 File exists: {config_path.exists()}")

        assert success, "❌ Save should succeed"
        assert config_path.exists(), "❌ File should exist"

        # Verify content
        with open(config_path, "r") as f:
            loaded = json.load(f)

        print(f"📝 Loaded content: {loaded}")

        assert loaded == test_config, "❌ Content should match"

        print("\n✅ TEST 4 PASSED: Config saved correctly")
        return True


def test_remove_from_existing_config():
    """Test 5: Remove mcp-browser from existing config with other servers."""
    print("\n" + "=" * 70)
    print("TEST 5: Remove from config with other servers")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create config with mcp-browser and other server
        test_config = {
            "mcpServers": {
                "mcp-browser": {"command": "mcp-browser", "args": ["mcp"]},
                "other-server": {"command": "other", "args": ["arg"]},
            }
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        print(f"\n📝 Before removal:\n{json.dumps(test_config, indent=2)}")

        # Remove mcp-browser
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        # Load and check
        with open(config_path, "r") as f:
            updated = json.load(f)

        print(f"\n📝 After removal:\n{json.dumps(updated, indent=2)}")

        assert success, "❌ Removal should succeed"
        assert "mcp-browser" not in updated["mcpServers"], (
            "❌ mcp-browser should be removed"
        )
        assert "other-server" in updated["mcpServers"], "❌ other-server should remain"

        print("\n✅ TEST 5 PASSED: Removed mcp-browser, preserved other servers")
        return True


def test_remove_when_not_configured():
    """Test 6: Remove when mcp-browser is not configured."""
    print("\n" + "=" * 70)
    print("TEST 6: Remove when not configured")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create config WITHOUT mcp-browser
        test_config = {
            "mcpServers": {"other-server": {"command": "other", "args": ["arg"]}}
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        print(f"\n📝 Config:\n{json.dumps(test_config, indent=2)}")

        # Try to remove mcp-browser
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        assert not success, "❌ Removal should return False when not found"

        print("\n✅ TEST 6 PASSED: Returns False when not configured")
        return True


def test_remove_nonexistent_file():
    """Test 7: Remove when config file doesn't exist."""
    print("\n" + "=" * 70)
    print("TEST 7: Remove when config file doesn't exist")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.json"

        print(f"\n📝 File exists: {config_path.exists()}")

        # Try to remove from non-existent file
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        assert not success, "❌ Removal should return False for non-existent file"

        print("\n✅ TEST 7 PASSED: Returns False for non-existent file")
        return True


def test_remove_no_mcpservers_section():
    """Test 8: Remove when config has no mcpServers section."""
    print("\n" + "=" * 70)
    print("TEST 8: Remove when no mcpServers section")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create config WITHOUT mcpServers section
        test_config = {"someOtherKey": "value"}

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        print(f"\n📝 Config:\n{json.dumps(test_config, indent=2)}")

        # Try to remove mcp-browser
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        assert not success, "❌ Removal should return False when no mcpServers section"

        print("\n✅ TEST 8 PASSED: Returns False when no mcpServers section")
        return True


def test_remove_empty_mcpservers():
    """Test 9: Remove from empty mcpServers section."""
    print("\n" + "=" * 70)
    print("TEST 9: Remove from empty mcpServers section")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create config with empty mcpServers
        test_config = {"mcpServers": {}}

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        print(f"\n📝 Config:\n{json.dumps(test_config, indent=2)}")

        # Try to remove mcp-browser
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        assert not success, "❌ Removal should return False for empty mcpServers"

        print("\n✅ TEST 9 PASSED: Returns False for empty mcpServers")
        return True


def test_remove_only_mcp_browser():
    """Test 10: Remove when mcp-browser is the only server."""
    print("\n" + "=" * 70)
    print("TEST 10: Remove when mcp-browser is only server")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        # Create config with ONLY mcp-browser
        test_config = {
            "mcpServers": {"mcp-browser": {"command": "mcp-browser", "args": ["mcp"]}}
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        print(f"\n📝 Before removal:\n{json.dumps(test_config, indent=2)}")

        # Remove mcp-browser
        success = remove_from_mcp_config(config_path)

        print(f"\n📝 Removal success: {success}")

        # Load and check
        with open(config_path, "r") as f:
            updated = json.load(f)

        print(f"\n📝 After removal:\n{json.dumps(updated, indent=2)}")

        assert success, "❌ Removal should succeed"
        assert "mcp-browser" not in updated["mcpServers"], (
            "❌ mcp-browser should be removed"
        )
        assert updated["mcpServers"] == {}, "❌ mcpServers should be empty"
        assert "mcpServers" in updated, "❌ mcpServers section should still exist"

        print("\n✅ TEST 10 PASSED: Removed only server, left empty mcpServers")
        return True


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "=" * 70)
    print("🧪 UNINSTALL HELPER FUNCTIONS UNIT TEST SUITE")
    print("=" * 70)

    tests = [
        test_load_existing_config,
        test_load_nonexistent_config,
        test_load_invalid_json,
        test_save_config,
        test_remove_from_existing_config,
        test_remove_when_not_configured,
        test_remove_nonexistent_file,
        test_remove_no_mcpservers_section,
        test_remove_empty_mcpservers,
        test_remove_only_mcp_browser,
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
