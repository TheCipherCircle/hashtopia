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
import yaml

# Project configurations
PROJECTS = {
    "spellengine": {
        "name": "SpellEngine / Dread Citadel",
        "basePath": "/Users/petermckernan/Projects/SpellEngine",
        "categories": {
            # Art assets - Dread Citadel art is in a single folder
            "dread_citadel_art": {
                "path": "assets/images/dread_citadel",
                "reviewType": "art",
                "patterns": ["*.png", "*.jpg"]
            },
            "dread_citadel_crunched": {
                "path": "assets/images/dread_citadel_crunched",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            # Audio assets
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
            # Narrative content
            "campaign_narrative": {
                "path": "content/adventures/dread_citadel",
                "reviewType": "narrative",
                "patterns": ["campaign.json", "campaign.yaml"],
                "extractContent": True
            },
            "encounters": {
                "path": "content/adventures/dread_citadel/encounters",
                "reviewType": "narrative",
                "patterns": ["*.yaml", "*.yml"],
                "extractContent": True
            },
            "dialogues": {
                "path": "content/dialogues",
                "reviewType": "narrative",
                "patterns": ["*.yaml", "*.json"],
                "extractContent": True
            },
            # Lore content
            "lore": {
                "path": "cipher-circle/stories",
                "reviewType": "lore",
                "patterns": ["*.md"]
            },
            "chronicles": {
                "path": "cipher-circle/chronicles",
                "reviewType": "lore",
                "patterns": ["*.md"]
            },
            # Voice/Vocal direction
            "voice_guides": {
                "path": "cipher-circle",
                "reviewType": "vocal",
                "patterns": ["VOICE_GUIDE.md", "*voice*.md"]
            }
        }
    },
    "hashchampions": {
        "name": "HashChampions",
        "basePath": "/Users/petermckernan/Projects/HashChampions",
        "categories": {
            # Art assets
            "hero": {
                "path": "assets/images/hero",
                "reviewType": "art",
                "patterns": ["*.png", "*.jpg"]
            },
            "leaderboard": {
                "path": "assets/images/leaderboard",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "ranks": {
                "path": "assets/images/icons/ranks",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "achievements": {
                "path": "assets/images/icons/achievements",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "profile": {
                "path": "assets/images/profile",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "characters": {
                "path": "assets/images/characters",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "equipment": {
                "path": "assets/images/icons/equipment",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "badges": {
                "path": "assets/images/icons/badges",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "scenes": {
                "path": "assets/images/scenes",
                "reviewType": "art",
                "patterns": ["*.png"]
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
            "special": {
                "path": "assets/images/special",
                "reviewType": "art",
                "patterns": ["*.png"]
            },
            "logos": {
                "path": "assets/images/logos",
                "reviewType": "art",
                "patterns": ["*.png", "*.svg"]
            },
            # Narrative/Flavor content
            "flavor_text": {
                "path": "content/narrative",
                "reviewType": "narrative",
                "patterns": ["flavor_text.json"],
                "extractContent": True
            },
            "weekly_themes": {
                "path": "content/narrative",
                "reviewType": "narrative",
                "patterns": ["weekly_themes.json"],
                "extractContent": True
            },
            # Audio
            "review_music": {
                "path": "assets/review/music",
                "reviewType": "audio",
                "patterns": ["*.mp3"]
            }
        }
    }
}


def extract_narrative_items(filepath: Path) -> list:
    """Extract reviewable text segments from JSON/YAML files."""
    items = []

    try:
        if filepath.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Campaign.json - extract chapter intros, encounters, dialogue
            if 'chapters' in data:
                for chapter in data.get('chapters', []):
                    if chapter.get('intro_text'):
                        items.append({
                            "type": "chapter_intro",
                            "text": chapter.get('intro_text', ''),
                            "context": f"Chapter {chapter.get('number', '?')}: {chapter.get('title', 'Untitled')}",
                            "id": f"chapter_{chapter.get('number', 0)}_intro"
                        })
                    for encounter in chapter.get('encounters', []):
                        if encounter.get('intro_text'):
                            items.append({
                                "type": "encounter_intro",
                                "text": encounter.get('intro_text', ''),
                                "context": f"{chapter.get('title', '')} > {encounter.get('title', 'Untitled')}",
                                "id": f"encounter_{encounter.get('id', 'unknown')}_intro"
                            })
                        # Extract hints
                        for i, hint in enumerate(encounter.get('hints', []), 1):
                            items.append({
                                "type": "hint",
                                "text": hint,
                                "context": f"{encounter.get('title', 'Untitled')} - Hint {i}",
                                "id": f"encounter_{encounter.get('id', 'unknown')}_hint_{i}",
                                "hintLevel": i
                            })

            # Flavor text JSON
            elif 'weekly' in data or 'monthly' in data or 'victory' in data:
                for category, entries in data.items():
                    if isinstance(entries, list):
                        for i, entry in enumerate(entries):
                            text = entry.get('text', entry) if isinstance(entry, dict) else entry
                            items.append({
                                "type": "flavor",
                                "text": text,
                                "context": f"{category.title()} #{i + 1}",
                                "id": f"flavor_{category}_{i + 1}",
                                "flavorCategory": category
                            })
                    elif isinstance(entries, dict):
                        for key, text in entries.items():
                            items.append({
                                "type": "flavor",
                                "text": text if isinstance(text, str) else str(text),
                                "context": f"{category.title()} - {key}",
                                "id": f"flavor_{category}_{key}",
                                "flavorCategory": category
                            })

            # Weekly themes JSON
            elif 'themes' in data or 'weeks' in data:
                themes = data.get('themes', data.get('weeks', []))
                for i, theme in enumerate(themes):
                    if isinstance(theme, dict):
                        items.append({
                            "type": "weekly_theme",
                            "text": theme.get('text', theme.get('description', '')),
                            "context": f"Week {theme.get('week', i + 1)}: {theme.get('title', '')}",
                            "id": f"week_{theme.get('week', i + 1)}",
                            "week": theme.get('week', i + 1)
                        })
                    elif isinstance(theme, str):
                        items.append({
                            "type": "weekly_theme",
                            "text": theme,
                            "context": f"Week {i + 1}",
                            "id": f"week_{i + 1}",
                            "week": i + 1
                        })

            # Generic dialogue JSON
            elif 'dialogues' in data or 'lines' in data:
                dialogues = data.get('dialogues', data.get('lines', []))
                for i, dialogue in enumerate(dialogues):
                    if isinstance(dialogue, dict):
                        items.append({
                            "type": "dialogue",
                            "text": dialogue.get('text', dialogue.get('line', '')),
                            "context": dialogue.get('speaker', dialogue.get('character', 'Unknown')),
                            "id": f"dialogue_{dialogue.get('id', i)}",
                            "speaker": dialogue.get('speaker', dialogue.get('character', ''))
                        })

        elif filepath.suffix in ['.yaml', '.yml']:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return items

            # Encounter YAML
            if 'intro_text' in data or 'title' in data:
                if data.get('intro_text'):
                    items.append({
                        "type": "encounter_intro",
                        "text": data.get('intro_text', ''),
                        "context": data.get('title', filepath.stem),
                        "id": f"encounter_{data.get('id', filepath.stem)}_intro"
                    })
                if data.get('success_text'):
                    items.append({
                        "type": "encounter_success",
                        "text": data.get('success_text', ''),
                        "context": f"{data.get('title', filepath.stem)} - Success",
                        "id": f"encounter_{data.get('id', filepath.stem)}_success"
                    })
                if data.get('failure_text'):
                    items.append({
                        "type": "encounter_failure",
                        "text": data.get('failure_text', ''),
                        "context": f"{data.get('title', filepath.stem)} - Failure",
                        "id": f"encounter_{data.get('id', filepath.stem)}_failure"
                    })
                # Extract hints
                for i, hint in enumerate(data.get('hints', []), 1):
                    hint_text = hint.get('text', hint) if isinstance(hint, dict) else hint
                    items.append({
                        "type": "hint",
                        "text": hint_text,
                        "context": f"{data.get('title', filepath.stem)} - Hint {i}",
                        "id": f"encounter_{data.get('id', filepath.stem)}_hint_{i}",
                        "hintLevel": i
                    })
                # Extract dialogue segments
                for dialogue in data.get('dialogue', data.get('dialogues', [])):
                    if isinstance(dialogue, dict):
                        items.append({
                            "type": "dialogue",
                            "text": dialogue.get('text', dialogue.get('line', '')),
                            "context": f"{data.get('title', filepath.stem)} - {dialogue.get('speaker', 'Unknown')}",
                            "id": f"dialogue_{data.get('id', filepath.stem)}_{dialogue.get('id', len(items))}",
                            "speaker": dialogue.get('speaker', dialogue.get('character', ''))
                        })

            # Dialogue YAML file
            elif 'npc' in data or 'character' in data or 'speaker' in data:
                speaker = data.get('npc', data.get('character', data.get('speaker', filepath.stem)))
                for i, line in enumerate(data.get('lines', data.get('dialogue', []))):
                    text = line.get('text', line) if isinstance(line, dict) else line
                    items.append({
                        "type": "dialogue",
                        "text": text,
                        "context": f"{speaker} - Line {i + 1}",
                        "id": f"dialogue_{filepath.stem}_{i}",
                        "speaker": speaker
                    })

    except Exception as e:
        print(f"    Warning: Could not parse {filepath}: {e}")

    return items


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
            extract_content = category.get("extractContent", False)

            for filepath in files:
                rel_path = filepath.relative_to(base_path)
                info = get_file_info(filepath)

                # For content files, extract individual reviewable items
                if extract_content and filepath.suffix in ['.json', '.yaml', '.yml']:
                    narrative_items = extract_narrative_items(filepath)
                    if narrative_items:
                        for item in narrative_items:
                            assets.append({
                                "name": item.get("id", f"{filepath.stem}_{len(assets)}"),
                                "path": str(rel_path),
                                "absolutePath": str(filepath),
                                "reviewType": category["reviewType"],
                                "contentType": item.get("type", "text"),
                                "text": item.get("text", ""),
                                "context": item.get("context", ""),
                                "speaker": item.get("speaker", ""),
                                "hintLevel": item.get("hintLevel"),
                                "flavorCategory": item.get("flavorCategory"),
                                "week": item.get("week"),
                                **info
                            })
                    else:
                        # Fall back to file-level entry if no items extracted
                        assets.append({
                            "name": filepath.name,
                            "path": str(rel_path),
                            "absolutePath": str(filepath),
                            "reviewType": category["reviewType"],
                            "contentType": "file",
                            **info
                        })
                else:
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
                    "extractContent": extract_content,
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
