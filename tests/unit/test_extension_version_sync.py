"""Tests for extension version synchronization."""

import json
import tempfile
from pathlib import Path

import pytest

from src.cli.utils.extension import get_extension_version, sync_extension_version


@pytest.fixture
def mock_extension_dir():
    """Create a temporary extension directory with manifest.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ext_dir = Path(tmpdir) / "extension"
        ext_dir.mkdir()

        # Create a manifest.json with old version
        manifest = {
            "manifest_version": 3,
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "Test extension",
        }

        manifest_path = ext_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        yield ext_dir


def test_get_extension_version_success(mock_extension_dir):
    """Test getting version from manifest.json."""
    version = get_extension_version(mock_extension_dir)
    assert version == "1.0.0"


def test_get_extension_version_missing_manifest():
    """Test getting version when manifest.json doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ext_dir = Path(tmpdir)
        version = get_extension_version(ext_dir)
        assert version is None


def test_sync_extension_version_updates(mock_extension_dir, monkeypatch):
    """Test that sync updates manifest.json version to match package version."""
    # Mock __version__ from _version.py
    from src import _version

    monkeypatch.setattr(_version, "__version__", "2.2.36")

    # Verify initial version is different
    assert get_extension_version(mock_extension_dir) == "1.0.0"

    # Sync version
    result = sync_extension_version(mock_extension_dir, quiet=True)
    assert result is True  # Should return True when version was updated

    # Verify version was updated
    assert get_extension_version(mock_extension_dir) == "2.2.36"


def test_sync_extension_version_already_synced(mock_extension_dir, monkeypatch):
    """Test that sync returns False when version is already up-to-date."""
    from src import _version

    # Set package version to match manifest version
    monkeypatch.setattr(_version, "__version__", "1.0.0")

    # Sync version
    result = sync_extension_version(mock_extension_dir, quiet=True)
    assert result is False  # Should return False when no update needed


def test_sync_extension_version_preserves_other_fields(mock_extension_dir, monkeypatch):
    """Test that sync only updates version field, preserving other fields."""
    from src import _version

    monkeypatch.setattr(_version, "__version__", "2.2.36")

    # Read original manifest
    manifest_path = mock_extension_dir / "manifest.json"
    with open(manifest_path, "r") as f:
        original_manifest = json.load(f)

    # Sync version
    sync_extension_version(mock_extension_dir, quiet=True)

    # Read updated manifest
    with open(manifest_path, "r") as f:
        updated_manifest = json.load(f)

    # Verify only version changed
    assert updated_manifest["manifest_version"] == original_manifest["manifest_version"]
    assert updated_manifest["name"] == original_manifest["name"]
    assert updated_manifest["description"] == original_manifest["description"]
    assert updated_manifest["version"] == "2.2.36"  # Only this should change


def test_sync_extension_version_missing_manifest():
    """Test that sync handles missing manifest.json gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ext_dir = Path(tmpdir)
        result = sync_extension_version(ext_dir, quiet=True)
        assert result is False
