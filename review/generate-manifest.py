#!/usr/bin/env python3
"""
QA Portal Manifest Generator

Scans asset directories and generates a manifest.json for the QA Portal.
Run this before each release to capture all reviewable assets.

Usage:
    python generate-manifest.py [--project PROJECT]

    --project: spellengine, hashchampions, or all (default: all)
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
import argparse

# Project configurations
PROJECTS = {
    "spellengine": {
        "name": "SpellEngine / Dread Citadel",
        "basePath": "/Users/petermckernan/Projects/SpellEngine",
        "categories": {
            "backgrounds": {
                "path": "assets/images/backgrounds",
                "reviewType": "art",
                "patterns": ["*.png", "*.jpg"]
            },
            "sprites": {
                "path": "assets/images/sprites",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "ui": {
                "path": "assets/images/ui",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "chapter_art": {
                "path": "assets/images/chapters",
                "reviewType": "art",
                "patterns": ["*.png", "*.jpg"]
            },
            "music": {
                "path": "assets/audio/music",
                "reviewType": "audio",
                "patterns": ["*.ogg", "*.mp3", "*.wav"]
            },
            "sfx": {
                "path": "assets/audio/sfx",
                "reviewType": "audio",
                "patterns": ["*.ogg", "*.mp3", "*.wav"]
            },
            "encounters": {
                "path": "content/adventures/dread_citadel/encounters",
                "reviewType": "narrative",
                "patterns": ["*.yaml", "*.yml"]
            }
        }
    },
    "hashchampions": {
        "name": "HashChampions",
        "basePath": "/Users/petermckernan/Projects/HashChampions",
        "categories": {
            "hero": {
                "path": "public/images/hero",
                "reviewType": "art",
                "patterns": ["*.png", "*.jpg"]
            },
            "leaderboard": {
                "path": "public/images/leaderboard",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "ranks": {
                "path": "public/images/icons/ranks",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "achievements": {
                "path": "public/images/icons/achievements",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "profile": {
                "path": "public/images/profile",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "characters": {
                "path": "public/images/characters",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "equipment": {
                "path": "public/images/equipment",
                "reviewType": "art",
                "patterns": ["*.png"]
            }
        }
    }
}


def get_file_info(filepath: Path) -> dict:
    """Get metadata for a file."""
    stat = filepath.stat()

    # Calculate MD5 for change detection
    with open(filepath, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()[:8]

    # Get dimensions for images
    dimensions = None
    if filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                dimensions = f"{img.width}x{img.height}"
        except ImportError:
            pass  # PIL not available
        except Exception:
            pass  # Can't read image

    return {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "hash": md5,
        "dimensions": dimensions
    }


def scan_directory(base_path: Path, category_path: str, patterns: list) -> list:
    """Scan a directory for matching files."""
    full_path = base_path / category_path

    if not full_path.exists():
        return []

    files = []
    for pattern in patterns:
        files.extend(full_path.glob(pattern))
        # Also check subdirectories
        files.extend(full_path.glob(f"**/{pattern}"))

    # Remove duplicates and sort
    files = sorted(set(files))
    return files


def generate_manifest(projects: list = None) -> dict:
    """Generate the full manifest."""

    if projects is None:
        projects = list(PROJECTS.keys())

    manifest = {
        "generated": datetime.now().isoformat(),
        "generator": "generate-manifest.py",
        "version": "1.0",
        "projects": {}
    }

    total_assets = 0

    for project_key in projects:
        if project_key not in PROJECTS:
            print(f"Warning: Unknown project '{project_key}'")
            continue

        project = PROJECTS[project_key]
        base_path = Path(project["basePath"])

        if not base_path.exists():
            print(f"Warning: Project path not found: {base_path}")
            continue

        project_data = {
            "name": project["name"],
            "basePath": str(base_path),
            "categories": {},
            "totalAssets": 0
        }

        for cat_key, category in project["categories"].items():
            files = scan_directory(base_path, category["path"], category["patterns"])

            if not files:
                continue

            assets = []
            for filepath in files:
                rel_path = filepath.relative_to(base_path)
                info = get_file_info(filepath)

                assets.append({
                    "name": filepath.name,
                    "path": str(rel_path),
                    "absolutePath": str(filepath),
                    "reviewType": category["reviewType"],
                    **info
                })

            if assets:
                project_data["categories"][cat_key] = {
                    "path": category["path"],
                    "reviewType": category["reviewType"],
                    "assets": assets,
                    "count": len(assets)
                }
                project_data["totalAssets"] += len(assets)
                total_assets += len(assets)

        manifest["projects"][project_key] = project_data

    manifest["totalAssets"] = total_assets

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Generate QA Portal manifest")
    parser.add_argument("--project", "-p",
                        choices=list(PROJECTS.keys()) + ["all"],
                        default="all",
                        help="Project to scan (default: all)")
    parser.add_argument("--output", "-o",
                        default="manifest.json",
                        help="Output file (default: manifest.json)")

    args = parser.parse_args()

    projects = None if args.project == "all" else [args.project]

    print("=" * 60)
    print("   QA PORTAL MANIFEST GENERATOR")
    print("=" * 60)
    print()

    manifest = generate_manifest(projects)

    # Write manifest
    output_path = Path(__file__).parent / args.output
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated: {manifest['generated']}")
    print()

    for proj_key, proj_data in manifest["projects"].items():
        print(f"  {proj_data['name']}")
        print(f"  {'─' * 40}")
        for cat_key, cat_data in proj_data["categories"].items():
            print(f"    {cat_key}: {cat_data['count']} assets")
        print(f"    TOTAL: {proj_data['totalAssets']}")
        print()

    print("=" * 60)
    print(f"  GRAND TOTAL: {manifest['totalAssets']} assets")
    print(f"  Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
