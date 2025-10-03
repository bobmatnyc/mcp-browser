#!/usr/bin/env python3
"""Build script for Chrome extension with version management and packaging."""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ExtensionBuilder:
    """Chrome extension build and version management."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.extension_dir = self.project_root / "src" / "extension"
        self.dist_dir = self.project_root / "dist"
        self.manifest_path = self.extension_dir / "manifest.json"
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.version_cache_path = self.project_root / ".claude/agents/.extension_build_cache"

        # Files to exclude from build
        self.exclude_patterns = [
            "create_icons.html",
            "*.test.js",
            "*.spec.js",
            ".DS_Store",
            "Thumbs.db",
            "*.map",
            "*.log",
            "*-enhanced.*"  # Exclude enhanced versions during development
        ]

    def get_current_version(self) -> str:
        """Get current version from manifest.json."""
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest.get('version', '0.0.0')

    def get_project_version(self) -> str:
        """Get current version from pyproject.toml."""
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
        return '0.0.0'

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string."""
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(map(int, parts))

    def format_version(self, major: int, minor: int, patch: int) -> str:
        """Format version tuple as string."""
        return f"{major}.{minor}.{patch}"

    def increment_version(self, version: str, bump_type: str) -> str:
        """Increment version based on bump type."""
        major, minor, patch = self.parse_version(version)

        if bump_type == 'patch':
            patch += 1
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return self.format_version(major, minor, patch)

    def update_manifest_version(self, new_version: str):
        """Update version in manifest.json."""
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        manifest['version'] = new_version

        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            f.write('\n')  # Add newline at end

        print(f"✅ Updated manifest.json version to {new_version}")

    def update_pyproject_version(self, new_version: str):
        """Update version in pyproject.toml."""
        with open(self.pyproject_path, 'r') as f:
            content = f.read()

        # Update version in pyproject.toml
        content = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            count=1,
            flags=re.MULTILINE
        )

        with open(self.pyproject_path, 'w') as f:
            f.write(content)

        print(f"✅ Updated pyproject.toml version to {new_version}")

    def get_extension_files(self) -> List[Path]:
        """Get list of files to include in extension build."""
        files = []

        # Read manifest to determine which files to include
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        # Add manifest itself
        files.append(self.manifest_path)

        # Add background script
        if 'background' in manifest:
            bg_script = manifest['background'].get('service_worker')
            if bg_script:
                bg_path = self.extension_dir / bg_script
                if bg_path.exists():
                    files.append(bg_path)

        # Add content scripts
        if 'content_scripts' in manifest:
            for content_script in manifest['content_scripts']:
                for js_file in content_script.get('js', []):
                    js_path = self.extension_dir / js_file
                    if js_path.exists():
                        files.append(js_path)

        # Add popup files
        if 'action' in manifest:
            popup_file = manifest['action'].get('default_popup')
            if popup_file:
                popup_path = self.extension_dir / popup_file
                if popup_path.exists():
                    files.append(popup_path)
                    # Also add corresponding JS file
                    popup_js = popup_file.replace('.html', '.js')
                    popup_js_path = self.extension_dir / popup_js
                    if popup_js_path.exists():
                        files.append(popup_js_path)
                    # Check for CSS file
                    popup_css = popup_file.replace('.html', '.css')
                    popup_css_path = self.extension_dir / popup_css
                    if popup_css_path.exists():
                        files.append(popup_css_path)

        # Add icon files
        icon_files = set()

        # Icons from action
        if 'action' in manifest and 'default_icon' in manifest['action']:
            for icon in manifest['action']['default_icon'].values():
                icon_files.add(icon)

        # Icons from manifest
        if 'icons' in manifest:
            for icon in manifest['icons'].values():
                icon_files.add(icon)

        for icon_file in icon_files:
            icon_path = self.extension_dir / icon_file
            if icon_path.exists():
                files.append(icon_path)

        return files

    def should_exclude(self, filepath: Path) -> bool:
        """Check if file should be excluded from build."""
        name = filepath.name
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif name == pattern:
                return True
        return False

    def build(self, version: Optional[str] = None, save_info: bool = True) -> Path:
        """Build extension package."""
        if version is None:
            version = self.get_current_version()

        # Create dist directory if it doesn't exist
        self.dist_dir.mkdir(exist_ok=True)

        # Get files to include
        files = self.get_extension_files()

        # Filter out excluded files
        files = [f for f in files if not self.should_exclude(f)]

        # Create zip file
        zip_name = f"mcp-browser-extension-v{version}.zip"
        zip_path = self.dist_dir / zip_name

        print(f"\n📦 Building extension package: {zip_name}")
        print(f"📂 Including {len(files)} files:")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(files):
                # Add file to zip with relative path
                arcname = file_path.relative_to(self.extension_dir)
                zf.write(file_path, arcname)
                file_size = file_path.stat().st_size
                print(f"  ✓ {arcname} ({self._format_size(file_size)})")

        # Get final size
        final_size = zip_path.stat().st_size

        # Save build information for change detection
        if save_info:
            files_hash = self.calculate_files_hash()
            self.save_build_info(version, files_hash)

        print(f"\n✅ Build complete!")
        print(f"📊 Package details:")
        print(f"  • Version: {version}")
        print(f"  • Files: {len(files)}")
        print(f"  • Size: {self._format_size(final_size)}")
        print(f"  • Location: {zip_path}")

        return zip_path

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def has_uncommitted_changes(self) -> bool:
        """Check if extension directory has uncommitted changes."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain', 'src/extension/'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            # Filter out enhanced files and check if any real changes
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line and not any(pattern in line for pattern in ['-enhanced.', 'test_', '_test.']):
                    changes.append(line)
            return len(changes) > 0
        except subprocess.CalledProcessError:
            # If git fails, assume changes exist
            return True

    def get_last_build_info(self) -> Optional[Dict]:
        """Get information about the last build."""
        if not self.version_cache_path.exists():
            return None

        try:
            with open(self.version_cache_path, 'r') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            return None

    def save_build_info(self, version: str, files_hash: str):
        """Save current build information."""
        self.version_cache_path.parent.mkdir(parents=True, exist_ok=True)

        build_info = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'files_hash': files_hash
        }

        with open(self.version_cache_path, 'w') as f:
            json.dump(build_info, f, indent=2)

    def calculate_files_hash(self) -> str:
        """Calculate a hash of extension files for change detection."""
        import hashlib

        hasher = hashlib.md5()
        files = self.get_extension_files()

        for file_path in sorted(files):
            if not self.should_exclude(file_path):
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())

        return hasher.hexdigest()

    def detect_changes_since_last_build(self) -> bool:
        """Detect if there are changes since the last build."""
        last_build = self.get_last_build_info()

        if not last_build:
            print("  ℹ️  No previous build found")
            return True

        current_hash = self.calculate_files_hash()
        if current_hash != last_build.get('files_hash'):
            print(f"  ✓ Changes detected since last build (v{last_build.get('version', 'unknown')})")
            return True

        print(f"  ℹ️  No changes since last build (v{last_build.get('version', 'unknown')})")
        return False

    def sync_versions(self):
        """Sync extension version with project version."""
        project_version = self.get_project_version()
        manifest_version = self.get_current_version()

        if project_version != manifest_version:
            print(f"⚠️  Version mismatch detected:")
            print(f"  • Project version: {project_version}")
            print(f"  • Extension version: {manifest_version}")
            print(f"  Syncing to project version: {project_version}")
            self.update_manifest_version(project_version)
        else:
            print(f"✅ Versions are in sync: {project_version}")

    def clean(self):
        """Clean dist directory of zip files."""
        if self.dist_dir.exists():
            zip_files = list(self.dist_dir.glob("mcp-browser-extension-*.zip"))
            if zip_files:
                print(f"🧹 Cleaning {len(zip_files)} extension packages...")
                for zip_file in zip_files:
                    zip_file.unlink()
                    print(f"  ✓ Removed {zip_file.name}")
            else:
                print("✅ No extension packages to clean")
        else:
            print("✅ Dist directory does not exist")


def main():
    """Main entry point for build script."""
    import argparse

    parser = argparse.ArgumentParser(description='Chrome Extension Build Tool')
    parser.add_argument('command', nargs='?', default='build',
                        choices=['build', 'release', 'version', 'sync', 'clean', 'info'],
                        help='Command to execute')
    parser.add_argument('--auto-version', action='store_true',
                        help='Auto-increment patch version if changes detected')
    parser.add_argument('--bump', choices=['patch', 'minor', 'major'], default='patch',
                        help='Version bump type (default: patch)')

    # Handle old-style version command (backward compatibility)
    if len(sys.argv) >= 3 and sys.argv[1] == 'version' and sys.argv[2] in ['patch', 'minor', 'major']:
        args = parser.parse_args(['version'])
        args.bump = sys.argv[2]
    else:
        args = parser.parse_args()

    builder = ExtensionBuilder()

    try:
        if args.command == 'build':
            # Build with current version, optionally auto-increment if changes detected
            builder.sync_versions()

            if args.auto_version:
                print("🔍 Checking for changes...")
                if builder.detect_changes_since_last_build():
                    current_version = builder.get_project_version()
                    new_version = builder.increment_version(current_version, 'patch')
                    print(f"📈 Auto-incrementing version: {current_version} → {new_version}")

                    # Update both files
                    builder.update_manifest_version(new_version)
                    builder.update_pyproject_version(new_version)
                    builder.build(new_version)

                    print(f"\n🎉 Auto-versioned build complete: {new_version}")
                else:
                    print("ℹ️  No changes detected, building with current version")
                    builder.build()
            else:
                builder.build()

        elif args.command == 'release':
            # Release command: Always increment version and build
            current_version = builder.get_project_version()

            # Check for uncommitted changes as a warning
            if builder.has_uncommitted_changes():
                print("⚠️  Warning: Uncommitted changes detected in src/extension/")
                print("   Consider committing changes after the release")

            # Calculate new version
            new_version = builder.increment_version(current_version, args.bump)
            print(f"🚀 Releasing extension: {current_version} → {new_version}")

            # Update both files
            builder.update_manifest_version(new_version)
            builder.update_pyproject_version(new_version)

            # Build with new version
            builder.build(new_version)

            print(f"\n🎉 Release {args.bump} complete: {current_version} → {new_version}")
            print(f"📝 Don't forget to commit the version changes!")

        elif args.command == 'version':
            # Version command for manual bump (backward compatibility)
            bump_type = args.bump

            # Get current versions
            current_version = builder.get_project_version()
            print(f"Current version: {current_version}")

            # Calculate new version
            new_version = builder.increment_version(current_version, bump_type)
            print(f"New version: {new_version}")

            # Update both files
            builder.update_manifest_version(new_version)
            builder.update_pyproject_version(new_version)

            # Build with new version
            builder.build(new_version)

            print(f"\n🎉 Version {bump_type} complete: {current_version} → {new_version}")

        elif args.command == 'sync':
            # Just sync versions without building
            builder.sync_versions()

        elif args.command == 'clean':
            # Clean dist directory
            builder.clean()

        elif args.command == 'info':
            # Show version information
            manifest_version = builder.get_current_version()
            project_version = builder.get_project_version()
            last_build = builder.get_last_build_info()

            print("📊 Version Information:")
            print(f"  • Extension version: {manifest_version}")
            print(f"  • Project version: {project_version}")

            if manifest_version != project_version:
                print("  ⚠️  Versions are out of sync!")
            else:
                print("  ✅ Versions are in sync")

            if last_build:
                print(f"\n📅 Last Build:")
                print(f"  • Version: {last_build.get('version', 'unknown')}")
                print(f"  • Timestamp: {last_build.get('timestamp', 'unknown')}")

            # Check for changes
            print(f"\n🔍 Change Detection:")
            if builder.has_uncommitted_changes():
                print("  • Git status: Uncommitted changes in src/extension/")
            else:
                print("  • Git status: Clean")

            if builder.detect_changes_since_last_build():
                print("  • Build cache: Changes detected since last build")
            else:
                print("  • Build cache: No changes since last build")

        else:
            print(f"Error: Unknown command '{args.command}'")
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()