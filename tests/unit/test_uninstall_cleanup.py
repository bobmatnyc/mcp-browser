"""Unit tests for enhanced uninstall cleanup functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli.commands.install import (
    confirm_removal,
    create_backup,
    find_extension_directories,
    format_size,
    get_cleanup_summary,
    get_data_directories,
    get_directory_size,
    get_playwright_cache_dir,
    remove_data_directories,
    remove_extension_directories,
    remove_playwright_cache,
)


class TestDiscoveryFunctions:
    """Test discovery functions for finding directories."""

    def test_find_extension_directories_local_extension(self, tmp_path, monkeypatch):
        """Test 1: Find local mcp-browser-extension directory."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir = tmp_path / "mcp-browser-extension"
        ext_dir.mkdir()

        # Test
        result = find_extension_directories()

        # Assert
        assert len(result) == 1
        assert result[0] == ext_dir

    def test_find_extension_directories_mcp_extension(self, tmp_path, monkeypatch):
        """Test 2: Find .mcp-browser/extension directory."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir = tmp_path / ".mcp-browser" / "extension"
        ext_dir.mkdir(parents=True)

        # Test
        result = find_extension_directories()

        # Assert
        assert len(result) == 1
        assert result[0] == ext_dir

    def test_find_extension_directories_both(self, tmp_path, monkeypatch):
        """Test 3: Find both extension directories."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir1 = tmp_path / "mcp-browser-extension"
        ext_dir1.mkdir()
        ext_dir2 = tmp_path / ".mcp-browser" / "extension"
        ext_dir2.mkdir(parents=True)

        # Test
        result = find_extension_directories()

        # Assert
        assert len(result) == 2
        assert ext_dir1 in result
        assert ext_dir2 in result

    def test_find_extension_directories_none(self, tmp_path, monkeypatch):
        """Test 4: Find no extension directories."""
        # Setup
        monkeypatch.chdir(tmp_path)

        # Test
        result = find_extension_directories()

        # Assert
        assert len(result) == 0

    def test_get_data_directories_global(self, tmp_path, monkeypatch):
        """Test 5: Find global .mcp-browser directory."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        global_mcp = tmp_path / ".mcp-browser"
        global_mcp.mkdir()
        (global_mcp / "data").mkdir()
        (global_mcp / "logs").mkdir()

        # Test
        result = get_data_directories()

        # Assert - should find subdirectories and parent
        assert len(result) > 0
        assert global_mcp in result

    def test_get_data_directories_local(self, tmp_path, monkeypatch):
        """Test 6: Find local .mcp-browser directory."""
        # Setup
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "fake_home")
        local_mcp = tmp_path / ".mcp-browser"
        local_mcp.mkdir()

        # Test
        result = get_data_directories()

        # Assert
        assert local_mcp in result

    def test_get_playwright_cache_dir_exists(self, tmp_path, monkeypatch):
        """Test 7: Find Playwright cache directory when it exists."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        cache_dir = tmp_path / ".cache" / "ms-playwright"
        cache_dir.mkdir(parents=True)

        # Test
        result = get_playwright_cache_dir()

        # Assert
        assert result == cache_dir

    def test_get_playwright_cache_dir_not_exists(self, tmp_path, monkeypatch):
        """Test 8: Return None when Playwright cache doesn't exist."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Test
        result = get_playwright_cache_dir()

        # Assert
        assert result is None


class TestSizeCalculations:
    """Test size calculation and formatting functions."""

    def test_get_directory_size(self, tmp_path):
        """Test 9: Calculate directory size correctly."""
        # Setup
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("x" * 100)
        (test_dir / "file2.txt").write_text("x" * 200)

        # Test
        size = get_directory_size(test_dir)

        # Assert
        assert size == 300

    def test_format_size_bytes(self):
        """Test 10: Format bytes correctly."""
        assert format_size(100) == "100.0 B"

    def test_format_size_kilobytes(self):
        """Test 11: Format kilobytes correctly."""
        assert format_size(2048) == "2.0 KB"

    def test_format_size_megabytes(self):
        """Test 12: Format megabytes correctly."""
        assert format_size(2 * 1024 * 1024) == "2.0 MB"


class TestCleanupSummary:
    """Test cleanup summary generation."""

    def test_get_cleanup_summary_extensions(self, tmp_path, monkeypatch):
        """Test 13: Generate summary for extensions."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir = tmp_path / "mcp-browser-extension"
        ext_dir.mkdir()
        (ext_dir / "test.txt").write_text("test")

        # Test
        summary = get_cleanup_summary(
            include_extensions=True, include_data=False, include_playwright=False
        )

        # Assert
        assert len(summary["directories"]) == 1
        assert str(ext_dir) in summary["directories"]
        assert summary["total_size"] > 0

    def test_get_cleanup_summary_empty(self):
        """Test 14: Generate empty summary when nothing to clean."""
        # Test
        summary = get_cleanup_summary(
            include_extensions=False, include_data=False, include_playwright=False
        )

        # Assert
        assert len(summary["directories"]) == 0
        assert summary["total_size"] == 0


class TestBackupFunctions:
    """Test backup functionality."""

    def test_create_backup_success(self, tmp_path):
        """Test 15: Successfully create backup."""
        # Setup
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("test content")

        backup_path = tmp_path / "backup"

        # Test
        result = create_backup([source_dir], backup_path)

        # Assert
        assert result is True
        assert (backup_path / "source" / "test.txt").exists()

    def test_create_backup_nonexistent_dir(self, tmp_path):
        """Test 16: Handle backup of non-existent directory gracefully."""
        # Setup
        source_dir = tmp_path / "nonexistent"
        backup_path = tmp_path / "backup"

        # Test
        result = create_backup([source_dir], backup_path)

        # Assert - should succeed but skip non-existent
        assert result is True


class TestRemovalFunctions:
    """Test removal functions."""

    def test_remove_extension_directories_dry_run(self, tmp_path, monkeypatch):
        """Test 17: Dry run doesn't actually remove directories."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir = tmp_path / "mcp-browser-extension"
        ext_dir.mkdir()
        (ext_dir / "test.txt").write_text("test")

        # Test
        count, errors = remove_extension_directories(dry_run=True)

        # Assert
        assert count == 1
        assert len(errors) == 0
        assert ext_dir.exists()  # Should still exist

    def test_remove_extension_directories_actual(self, tmp_path, monkeypatch):
        """Test 18: Actually remove directories."""
        # Setup
        monkeypatch.chdir(tmp_path)
        ext_dir = tmp_path / "mcp-browser-extension"
        ext_dir.mkdir()
        (ext_dir / "test.txt").write_text("test")

        # Test
        count, errors = remove_extension_directories(dry_run=False)

        # Assert
        assert count == 1
        assert len(errors) == 0
        assert not ext_dir.exists()

    def test_remove_data_directories_with_backup(self, tmp_path, monkeypatch):
        """Test 19: Remove data directories with backup."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / ".mcp-browser"
        data_dir.mkdir()
        (data_dir / "test.txt").write_text("test content")

        # Test
        count, errors = remove_data_directories(dry_run=False, backup=True)

        # Assert
        assert count > 0
        assert len(errors) == 0
        # Check backup was created
        backup_root = tmp_path / ".mcp-browser-backups"
        assert backup_root.exists()

    def test_remove_data_directories_no_backup(self, tmp_path, monkeypatch):
        """Test 20: Remove data directories without backup."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / ".mcp-browser"
        data_dir.mkdir()
        (data_dir / "test.txt").write_text("test content")

        # Test
        count, errors = remove_data_directories(dry_run=False, backup=False)

        # Assert
        assert count > 0
        assert len(errors) == 0
        # Check no backup was created
        backup_root = tmp_path / ".mcp-browser-backups"
        assert not backup_root.exists()

    def test_remove_playwright_cache_dry_run(self, tmp_path, monkeypatch):
        """Test 21: Playwright cache dry run."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        cache_dir = tmp_path / ".cache" / "ms-playwright"
        cache_dir.mkdir(parents=True)
        (cache_dir / "test.txt").write_text("test")

        # Test
        count, errors = remove_playwright_cache(dry_run=True)

        # Assert
        assert count == 1
        assert len(errors) == 0
        assert cache_dir.exists()

    def test_remove_playwright_cache_actual(self, tmp_path, monkeypatch):
        """Test 22: Actually remove Playwright cache."""
        # Setup
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        cache_dir = tmp_path / ".cache" / "ms-playwright"
        cache_dir.mkdir(parents=True)
        (cache_dir / "test.txt").write_text("test")

        # Test
        count, errors = remove_playwright_cache(dry_run=False)

        # Assert
        assert count == 1
        assert len(errors) == 0
        assert not cache_dir.exists()


class TestConfirmation:
    """Test confirmation prompts."""

    @patch("click.confirm")
    def test_confirm_removal_user_confirms(self, mock_confirm):
        """Test 23: User confirms removal."""
        # Setup
        mock_confirm.return_value = True
        items = ["/path/to/dir1", "/path/to/dir2"]

        # Test
        result = confirm_removal(items, "remove these items")

        # Assert
        assert result is True
        mock_confirm.assert_called_once()

    @patch("click.confirm")
    def test_confirm_removal_user_declines(self, mock_confirm):
        """Test 24: User declines removal."""
        # Setup
        mock_confirm.return_value = False
        items = ["/path/to/dir1"]

        # Test
        result = confirm_removal(items, "remove these items")

        # Assert
        assert result is False

    def test_confirm_removal_empty_list(self):
        """Test 25: Empty list returns False."""
        # Test
        result = confirm_removal([], "remove these items")

        # Assert
        assert result is False


def run_all_tests():
    """Run all tests with pytest."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()
