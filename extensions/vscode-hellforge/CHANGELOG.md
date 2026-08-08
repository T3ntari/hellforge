# Changelog

## [1.0.0] - 2026-07-31

### Added
- TextMate grammar for the E language (all syntax versions)
- Language server with autocomplete, hover, diagnostics, symbols, go-to-definition, formatting, signature help
- Python LSP bridge using the real HELLFORGE compiler
- 14 file icons (.e, .ei, .eic, .enx, .eci, .ec, .ee, .ecc, .mid, .wav, .mp3, .mp4, .machine, .human)
- 22 snippets (directives, play note/chord, machine lines, loops, projects)
- Commands: compile, play, open shell, windowed variants
- Keybindings: Ctrl+Shift+B (compile), Ctrl+Shift+P (play), Ctrl+Shift+E (shell)
- Editor title and explorer context menus

### Notes
- Requires HELLFORGE project root (ep.py) in the workspace
- Compile/play commands use the run.py launcher
