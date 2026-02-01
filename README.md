# hashtopia

Central QA & Operations hub for the Hashtopia ecosystem.

```
                          hashtopia.org
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    play.hashtopia.org  forge.hashtopia.org  knowledge.hashtopia.org
            │                  │                  │
   ┌────────┴────────┐         │                  │
   │                 │         │                  │
   ▼                 ▼         ▼                  ▼
SpellEngine    HashChampions  PatternForge    Docs/Wiki
```

## QA Portal

Interactive review system for all Hashtopia products.

```bash
# Serve locally
cd review
python3 -m http.server 8080

# Open
open http://localhost:8080/
```

### Features

- **Three View Modes**: List (triage), Grid (tiles), Detail (full review)
- **Image Annotations**: Draw circles, boxes, arrows on art assets
- **Knowledge Base Widget**: Suggest edits to knowledge.hashtopia.org
- **GitHub Integration**: Submit issues directly to agent queues
- **Autosave**: Never lose review progress

### Regenerate Asset Manifest

```bash
cd review
python3 generate-manifest.py
```

## Issue Templates

All QA feedback routes through GitHub Issues with proper agent queues:

| Template | Queue | Purpose |
|----------|-------|---------|
| art-review | ◈ Fraz | Visual assets |
| audio-review | ♪ Echo | Music, SFX |
| narrative-review | ≋ Mirth | Story, dialogue |
| puzzle-review | ⌘ Vex | Ciphers, challenges |
| ux-review | ◐ Prism | User experience |
| creative-review | ≋ Mirth | Playtest moments |
| bug-report | ⚒ Forge | Crashes, errors |
| balance-review | ☆ Jinx | XP, difficulty |
| lore-consistency | ◇ Loreth | Canon, timeline |
| accessibility | ◐ Prism | A11y issues |
| documentation | ◇ Loreth | Typos, unclear docs |
| patternforge-cli | ⚒ Forge | CLI feedback |

## Products Covered

- **SpellEngine / Dread Citadel** - Dark fantasy puzzle game
- **HashChampions** - Competitive hash cracking
- **PatternForge** - CLI tool suite
- **knowledge.hashtopia.org** - Documentation wiki
- **hashtopia.org** - Main website

---

*The Cipher Circle QA System*
