#!/usr/bin/env python3
"""Simple build script for browser extension distribution."""

import zipfile
from pathlib import Path
from typing import Optional


def build_extension(
    source_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    name: str = "mcp-browser-extension.zip"
) -> Optional[Path]:
    """Build extension ZIP from source directory.

    Args:
        source_dir: Extension source directory (defaults to mcp-browser-extension/)
        output_dir: Output directory for ZIP file (defaults to dist/)
        name: Name of output ZIP file

    Returns:
        Path to created ZIP file, or None if failed
    """
    # Default paths
    project_root = Path(__file__).parent.parent

    if source_dir is None:
        # Try multiple possible locations
        if (project_root / "mcp-browser-extension").exists():
            source_dir = project_root / "mcp-browser-extension"
        elif (project_root / "src" / "extension").exists():
            source_dir = project_root / "src" / "extension"
        else:
            print("❌ Error: Extension source directory not found")
            return None

    if output_dir is None:
        output_dir = project_root / "dist"

    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / name

    # Remove existing zip if present
    if zip_path.exists():
        zip_path.unlink()

    # Files to include in the extension
    extension_files = [
        "manifest.json",
        "background-enhanced.js",
        "content.js",
        "popup-enhanced.html",
        "popup-enhanced.js",
    ]

    try:
        print(f"📦 Building extension from: {source_dir}")
        print(f"📂 Output: {zip_path}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add individual files
            files_added = 0
            for pattern in extension_files:
                file_path = source_dir / pattern
                if file_path.exists():
                    zf.write(file_path, pattern)
                    files_added += 1
                    print(f"  ✓ {pattern}")
                else:
                    print(f"  ⚠ {pattern} (not found)")

            # Add icons directory
            icons_dir = source_dir / "icons"
            if icons_dir.exists():
                for icon_file in icons_dir.iterdir():
                    if icon_file.is_file():
                        zf.write(icon_file, f"icons/{icon_file.name}")
                        files_added += 1
                        print(f"  ✓ icons/{icon_file.name}")

        print(f"\n✅ Build complete: {files_added} files packaged")
        print(f"📊 Size: {zip_path.stat().st_size / 1024:.1f} KB")
        return zip_path

    except Exception as e:
        print(f"❌ Error packaging extension: {e}")
        return None


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build browser extension for distribution"
    )
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        help="Source directory (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output directory (default: dist/)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="mcp-browser-extension.zip",
        help="Output filename (default: mcp-browser-extension.zip)",
    )

    args = parser.parse_args()

    result = build_extension(
        source_dir=args.source,
        output_dir=args.output,
        name=args.name,
    )

    if result:
        print(f"\n🎉 Success! Extension ready at:")
        print(f"   {result}")
        return 0
    else:
        print("\n❌ Build failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
