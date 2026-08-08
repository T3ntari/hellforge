# HELLFORGE — E Language Support

**Made by Tentari.** Syntax highlighting, IntelliSense, autocomplete, live diagnostics, snippets, and file icons for the E language (HELLFORGE ecosystem).

## Features

### Syntax Highlighting
Full TextMate grammar covering every E construct:

- `@directives` (bpm, key, scale, vol, curve, ...)
- `#MACHINE` / `#HUMAN` / `#V3` / `#V4` mode directives
- Machine tokens `T N D V CH`
- Human mode `play note()` / `play chord()`
- `$variables`, `{math expressions}`, math functions
- `for` / `repeat` / `while` loops
- Chord qualities, duration codes, velocity codes, note names
- `//` and `/* */` comments

### IntelliSense (Language Server)

Powered by the **real E compiler** via a Python bridge (`lsp_bridge.py`):

| Feature | What you get |
|---------|--------------|
| Autocomplete | Directives, keywords, variables, math functions, chord qualities, note names, durations, velocities |
| Hover docs | Meaning of every token. `N60` → "Note C4 (MIDI 60)". |
| Signature help | `play chord(C, <|>)` suggests qualities |
| Live diagnostics | Compile errors + unrecognized lines as squiggles |
| Document symbols | Variables, modes, sections in the outline |
| Go to definition | Jump from `$var` usage to its definition |
| Formatting | Normalize machine lines with one click |

### File Icons

| Ext | Icon | Ext | Icon |
|-----|------|-----|------|
| `.e` | Golden note | `.eci` | Note + arrows |
| `.ei` | Folder + note | `.ec` | Gear + note |
| `.eic` | Split note | `.ee` | Note + lock |
| `.enx` | Stacked sheets | `.ecc` | Gear + lock + note |
| `.mid` | MIDI plug | `.wav` | Sound wave |
| `.mp3` | Wave + label | `.mp4` | Film + note |
| `.machine` | Bracket glyph | `.human` | Speech bubble |

### Commands

| Command | Shortcut |
|---------|----------|
| HELLFORGE: Compile to MIDI | `Ctrl+Shift+B` |
| HELLFORGE: Play | `Ctrl+Shift+P` |
| HELLFORGE: Open E Shell | `Ctrl+Shift+E` |
| HELLFORGE: Compile in New Window | — |
| HELLFORGE: Play in New Window | — |

Commands launch via the HELLFORGE `run.py` launcher — windowed or detached, your choice.

## Requirements

- Python 3.8+ with the HELLFORGE project (compiler at `ep.py`)
- Node.js (for the extension itself, bundled)
- Open a folder containing the HELLFORGE project root (`ep.py`)

## Installation

### From the Marketplace
Search **HELLFORGE** in the VS Code Extensions panel, or run:
```
code --install-extension tentari.hellforge-language
```

### From a VSIX
```
code --install-extension hellforge-language-1.0.0.vsix
```

### From source
```
cd extensions/vscode-hellforge
npm install
npm run compile
npx @vscode/vsce package
code --install-extension hellforge-language-1.0.0.vsix
```

## Usage

Open any `.e`, `.ei`, `.eic`, `.enx` file. Highlighting and IntelliSense activate automatically.

- Type `@` to see directives
- Type `$` to see defined variables
- Type `play chord(` to get quality suggestions
- Hover over any token for documentation
- `Ctrl+Shift+B` compiles the current file to MIDI

## Release Notes

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).

---

*HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS — Made by Tentari.*
