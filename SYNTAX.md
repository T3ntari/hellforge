# HELLFORGE v0.1.0-beta — E Language — Complete Tutorial & Reference

> **Open Source (MIT) | [GitHub](https://github.com/tentari/hellforge) | [Docs](doc/index.md)**
>
> **For everyone — no piano experience needed, no programming experience needed.**
> This guide teaches you music + the E language from absolute zero to advanced composer.

## What Is E?

E is a **domain-specific language for piano music composition**, now part of the **HELLFORGE ecosystem**. You write music as text — notes, chords, rhythms, dynamics — and E turns it into sound. HELLFORGE adds GPU-accelerated math (Radical), Tensor Core matrix ops (TensorSHARP), OpenGL/Vulkan graphics APIs, and 3D spatial audio on top of the E compiler.

```
@bpm 120
play note(C4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(G4) @dur:h @vel:ff
```

That's a complete piece of music. Three lines. A C major chord. You can play it immediately.

## Why E Exists

**Music is hard to write, but text is easy.** Most music software forces you to:
- Click around a graphical interface (slow)
- Learn complex DAWs (expensive)
- Use proprietary formats (locked in)

E gives you:
- **Plain text** — edit in any text editor, version control with git
- **One format, many outputs** — `.mid`, `.wav`, `.mp3`, `.mp4`, `.eic`, `.ec`, `.ee` from the same source
- **Precision** — you control every millisecond, every velocity, every pitch bend
- **Readability** — `play note(C4) @dur:q @vel:mf` is obvious even to non-musicians
- **AI-friendly** — language models can generate, analyze, and transform E natively
- **No gatekeeping** — free, open-source, runs on any computer

## Who Is This For?

| You are… | Start here |
|----------|------------|
| A complete beginner who has never touched a piano | Section 1 — we teach music from zero |
| A musician who wants to code their compositions | Section 4 (#MACHINE) or 5 (#HUMAN) |
| A developer who wants to generate music with AI | Section 4 and Section 50 (For AI Agents) |
| A composer with existing MIDI files | Section 35 (Import MIDI to E) |
| Someone who just wants to transcribe audio to notes | Section 36 (Import Audio to E) |
| An educator teaching music through code | Section 5 (#HUMAN) and Section 16 (v3 Shorthand) |

## The Main Goal

**E exists so that anyone — regardless of musical training, financial resources, or hardware — can compose, share, and protect original piano music using nothing but a text editor.**

The language is designed around three principles:

1. **Human-first syntax** — readable, learnable, teachable
2. **Machine precision** — exact control when you need it
3. **Zero friction** — write, compile, play. No setup, no subscriptions, no cloud.

Whether you're writing a lullaby for your child, generating an algorithmic etude, transcribing a recording of your grandmother playing, or building a 16-movement symphony with inherited sections — E is the tool that stays out of your way.

## Project Structure

```
HELLFORGE v1.0.0.0 ALPHA/
├── ep.py                    ← Compiler entry point (shim → ep_compiler/)
├── eshell.py                ← HELLFORGE interactive command shell
├── player.py                ← MIDI/audio player (console + GUI)
├── ep_core.py               ← Core system (signing, REGAS, encryption, GC, plugins)
├── ep_audio.py              ← Audio driver system
├── ep_pkg.py                ← Package manager (mods, plugins, registry)
├── ai.py                    ← AI composition assistant
├── SYNTAX.md                ← This document
├── doc/                     ← Full HELLFORGE wiki (60+ pages)
│   ├── index.md             ←   Wiki home page
│   ├── getting-started.md   ←   Quick start guide
│   ├── ...                  ←   See doc/index.md for full list
├── ep_compiler/             ← Modular compiler package
│   ├── compile.py           ←   Pipeline orchestrator
│   ├── events.py            ←   Event data structures
│   ├── formats.py           ←   Output format handlers
│   ├── directives.py        ←   @ directives parser
│   ├── import_midi.py       ←   MIDI → E converter
│   ├── audio_transcribe.py  ←   Audio → E FFT transcriber
│   ├── e_runtime.py         ←   .ei project interpreter
│   ├── mode_eci.py          ←   .eci toggleable-mode parser
│   ├── mode_enx.py          ←   .enx album index parser
│   ├── mode_v1_machine.py   ←   #MACHINE token parser
│   ├── mode_v1_human.py     ←   #HUMAN play() parser
│   ├── mode_v3_extended.py  ←   v3 shorthand + macro preprocessor
│   ├── mode_v4_polyrhythm.py ←  v4 polyrhythm and Euclidean rhythms
│   ├── scale_quantizer.py   ←   Scale quantization engine
│   ├── async_compile.py     ←   Async compile pipeline
│   └── math_engine.py       ←   Math expression tokenizer/AST
├── plugins/                 ← HELLFORGE plugin ecosystem
│   ├── radical/             ←   GPU Shader Math Core (priority 5)
│   ├── tensorsharp/         ←   Tensor Core acceleration (priority 3)
│   ├── openapi/             ←   OpenGL Graphics API
│   ├── vulkanizer/          ←   Vulkan Compute + Ray Tracing API
│   ├── eaudio/              ←   3D Spatial Audio API
│   ├── lure/                ←   LuaJIT Runtime Accelerator (priority 10)
│   ├── fentclient/          ←   Performance + Bug fixes + Security
│   ├── portbaby/            ←   Syntax version converter
│   └── talisman/            ←   Audio culling + privacy engine
├── embedded_plugins/        ← Signed backup of all plugins
│   ├── hellforge_plugins_backup.zip  ← Full backup (146 files, 137KB)
│   └── *.json               ←   Per-plugin embedded backups
├── tools/                   ← Standalone utilities
│   ├── e2midi.py            ←   E → MIDI converter
│   ├── midi2e.py            ←   MIDI → E converter
│   └── v2compiler.py        ←   Legacy syntax v2 compiler
├── examples/                ← Example compositions + game engine demo
│   ├── Rush_E.e             ←   Reference music piece
│   └── opengl_engine.py     ←   AAA game engine built on OPENapi+Vulkanizer+EAudio
└── tests/                   ← Full test suite (130+ tests)
    ├── syntax_test.py       ←   54 syntax + math + limit tests
    ├── async_test.py        ←   19 async compile tests
    ├── gpu_test.py          ←   34 GPU plugin + API tests
    └── verify_signing.py    ←   23 REGAS/TENTARI signing verification tests
```

## Quick Start

```powershell
# 1. Start the shell
py -3 eshell.py

# 2. Compile the demo
E ...> compile examples/Rush_E.e -o rush.mid

# 3. Listen
E ...> play rush.mid

# Or skip straight to playing — one command
E ...> play examples/Rush_E.e
```

That's it. You just played your first E composition.

For the full tutorial, start at [Section 1](#1-before-you-start--what-is-music).
For the HELLFORGE wiki (60+ pages), see [doc/index.md](doc/index.md).
For GPU/plugin/audio API docs, see the [Plugins section](#45-plugin--mod-system--extend-e).

---

## Table of Contents

1. [Before You Start — What Is Music?](#1-before-you-start--what-is-music)
2. [Installing & Your First Note](#2-installing--your-first-note)
3. [The E Shell — Your Command Center](#3-the-e-shell--your-command-center)
4. [#MACHINE Mode — The Precise Way](#4-machine-mode--the-precise-way)
5. [#HUMAN Mode — The Readable Way](#5-human-mode--the-readable-way)
6. [File Formats at a Glance](#6-file-formats-at-a-glance)
7. [Syntax Version Compatibility](#7-syntax-version-compatibility)
8. [Notes, Chords, and Scales — Music Theory for E](#8-notes-chords-and-scales--music-theory-for-e)
9. [Durations & Rhythm](#9-durations--rhythm)
10. [Velocity & Dynamics (Loud or Soft)](#10-velocity--dynamics-loud-or-soft)
11. [Multiple Notes at Once — Chords](#11-multiple-notes-at-once--chords)
12. [MIDI Note Reference (Piano Key Map)](#12-midi-note-reference-piano-key-map)
13. [BPM & Tempo](#13-bpm--tempo)
14. [Tempo Aliases (Italian Words)](#14-tempo-aliases-italian-words)
15. [Comments (Document Your Music)](#15-comments-document-your-music)
16. [v2 Semantic Syntax — Think in Music, Not Numbers](#16-v2-semantic-syntax--think-in-music-not-numbers)
17. [v3 Shorthand — Fast & Friendly](#17-v3-shorthand--fast--friendly)
18. [Macros — Reuse Patterns](#18-macros--reuse-patterns)
19. [Repeats — Play It Again](#19-repeats--play-it-again)
20. [Probability & Randomization — Add Surprise](#20-probability--randomization--add-surprise)
21. [Parallel Notation — Chords on One Line](#21-parallel-notation--chords-on-one-line)
22. [Key Modulation — Change Key Mid-Song](#22-key-modulation--change-key-mid-song)
23. [Scale Quantization — Snap Notes to a Scale](#23-scale-quantization--snap-notes-to-a-scale)
24. [Channel Binding — Multiple Instruments](#24-channel-binding--multiple-instruments)
25. [Tempo Curves — Speed Up / Slow Down](#25-tempo-curves--speed-up--slow-down)
26. [Polyrhythms & Euclidean Rhythms](#26-polyrhythms--euclidean-rhythms)
27. [Macro Transposition — Shift Notes Up/Down](#27-macro-transposition--shift-notes-updown)
28. [Dynamic Arcs — Get Louder Then Softer](#28-dynamic-arcs--get-louder-then-softer)
29. [Articulation — Staccato / Legato / Accent](#29-articulation--staccato--legato--accent)
30. [Roman Numeral Chords — I–IV–V–vi](#30-roman-numeral-chords--i-iv-v-vi)
31. [.ei Project Index — Multi-File Songs](#31-ei-project-index--multi-file-songs)
32. [.eci Mode-Toggle Files — One File, Both Syntaxes](#32-eci-mode-toggle-files--one-file-both-syntaxes)
33. [.enx Root Index — Albums & Ordered Playlists](#33-enx-root-index--albums--ordered-playlists)
34. [.ei Inheritance — Reuse Projects as Building Blocks](#34-ei-inheritance--reuse-projects-as-building-blocks)
35. [Import MIDI to E — Convert Any Song](#35-import-midi-to-e--convert-any-song)
36. [Import Audio to E — Transcribe from Sound](#36-import-audio-to-e--transcribe-from-sound)
37. [MIDI → Full Human Project](#37-midi--full-human-project)
38. [.ec Compiled Binary — Fast Load](#38-ec-compiled-binary--fast-load)
39. [.eic Clear Bundle — One File to Share](#39-eic-clear-bundle--one-file-to-share)
40. [Export to .wav / .mp3 / .mp4](#40-export-to-wav--mp3--mp4)
41. [Signing & Encryption — Protect Your Music](#41-signing--encryption--protect-your-work)
42. [Garbage Collection — Clean Up Messy Generations](#42-garbage-collection--clean-up-messy-generations)
43. [Low-Level Sound Control — For Perfectionists](#43-low-level-sound-control--for-perfectionists)
44. [Audio Driver System — Pick Your Output](#44-audio-driver-system--pick-your-output)
45. [HELLFORGE Ecosystem & CORE-EXPANSION: REGAS](#45-hellforge-ecosystem--core-expansion-regas)
46. [GPU Shader Math (Radical Plugin)](#46-gpu-shader-math-radical-plugin)
47. [Tensor Core Acceleration (TensorSHARP Plugin)](#47-tensor-core-acceleration-tensorsharp-plugin)
48. [OpenGL Graphics API (OPENapi Plugin)](#48-opengl-graphics-api-openapi-plugin)
49. [Vulkan Compute + Ray Tracing (Vulkanizer Plugin)](#49-vulkan-compute--ray-tracing-vulkanizer-plugin)
50. [3D Spatial Audio (EAudio Plugin)](#50-3d-spatial-audio-eaudio-plugin)
51. [LuaJIT Accelerator (LURE Plugin)](#51-luajit-accelerator-lure-plugin)
52. [Plugin & Mod System — Extend E](#52-plugin--mod-system--extend-e)
53. [EZip Packages](#53-ezip-packages)
54. [The Player (Console & GUI)](#54-the-player-console--gui)
55. [Troubleshooting](#55-troubleshooting)
56. [Command Reference](#56-command-reference)
57. [For AI Agents — How to Compose Music with E](#57-for-ai-agents--how-to-compose-music-with-e)
58. [Ethics & Attribution — Don't Steal Music](#58-ethics--attribution--dont-steal-music)
52. [Glossary](#52-glossary)
53. [MIT License](#53-mit-license)

---

## 1. Before You Start — What Is Music?

Music is organized sound. When you press a key on a piano, you hear a **note** — a specific pitch. If you press several keys in a row, that's a **melody**. If you press several at the same time, that's a **chord**.

The E language lets you describe music as text. You write **which notes to play, when to play them, how loud, and for how long**. The computer reads your text and makes sound.

### The Piano Keyboard

A piano has white and black keys. Each key makes a different pitch:

```
  C#  D#  F#  G#  A#  C#  D#  F#  G#  A#
 C   D   E   F   G   A   B   C   D   E   F ...
```

Middle C (the center of a piano) is called **C4**. The 4 means "octave 4". Each octave up doubles the frequency (sounds higher). Each octave down is lower.

### MIDI Numbers

In the computer world, each piano key has a number called **MIDI number**:

- C4 = MIDI 60 (the middle of a standard 88-key piano)
- D4 = MIDI 62
- E4 = MIDI 64
- Every time you go up one white key, add 2. Every black key is +1 from the white key before it.

But you don't need to memorize numbers — E has human-readable names too!

---

## 2. Installing & Your First Note

### What You Need

- Python 3.10 or newer
- Windows, Mac, or Linux

Open a terminal (Command Prompt, PowerShell, or Terminal) and navigate to the folder containing E:

```powershell
cd C:\path\to\piano-dsl
```

### Your First Music File

Create a file called `hello.e` with this content:

```
@bpm 120
T0 N60 D500 V0.8
```

This means: **At 120 BPM, play MIDI note 60 (C4) at time 0, for 500ms, at 80% volume.**

### Listen to It

```powershell
py -3 eshell.py
E ...> compile hello.e -o hello.mid
E ...> play hello.mid
```

You should hear a single piano note. You just made music with code.

---

## 3. The E Shell — Your Command Center

`eshell.py` is your control panel. It's a complete command-line environment with a futuristic look, 20+ built-in commands, aliases, plugin support, color-coded output, and file management.

### Starting the Shell

```powershell
py -3 eshell.py
```

You'll see:

```
╔══════════════════════════════╗
║      E SHELL v2.1           ║
╚══════════════════════════════╝
Type help for commands

E ...>
```

The prompt shows `E` followed by the current directory (truncated if long) and a `>`.

### How to Get Help

```
E ...> help           # Show all commands
E ...> ?              # Same as help
```

Type `help` or `?` at any time to see the full command list.

### Quick Start — Your First Session

```powershell
E ...> compile examples/Rush_E.e -o rush.mid   # Compile to MIDI
E ...> play rush.mid                            # Listen
```

The `compile` command reads the `.e` file, turns it into a MIDI file, then `play` sends it to your computer's MIDI synthesizer.

---

### All eshell Commands — Complete Reference

eshell has **22 built-in commands** plus any that plugins add dynamically. Many commands have aliases (shortcuts).

#### Navigation

| Command | Aliases | What It Does | Examples |
|---------|---------|-------------|----------|
| `cd` | `chdir` | Change directory | `cd examples`, `cd ..`, `cd /full/path` |
| `ls` | `dir` | List files (color-coded by type) | `ls`, `ls my_folder` |
| `clear` | `cls` | Clear screen and redisplay banner | `clear` |
| `exit` | `quit` | Quit the shell | `exit` |

**Color coding in `ls`:**
- Green: `.e`, `.ei`, `.eic` (source files)
- Yellow: `.mid`, `.wav`, `.mp3`, `.mp4` (playable)
- Red: `.ee`, `.ec`, `.ecc` (binary/encrypted)
- Magenta: `.py` (Python scripts)
- Cyan: directories
- Grey: everything else

#### Compilation & Conversion

| Command | Aliases | What It Does | Examples |
|---------|---------|-------------|----------|
| `compile` | `build` | Compile `.e`/`.ei`/`.eci`/`.enx` to any output format | `compile song.e -o song.mid` |
| `convert` | — | Import MIDI/audio to `.e`; compile `.e` to other formats; `--project` for full project | `convert song.mid -o song.e`, `convert song.mid --project` |
| `ecc` | — | Compile + encrypt in one step (`.e` → `.ecc`) | `ecc song.e -o song.ecc` |

**`compile` flags:**
- `-o <file>` — specify output path (default: input name + `.mid`)
- `--human` — convert #MACHINE tokens to #HUMAN syntax
- `--machine` — convert #HUMAN syntax to #MACHINE tokens
- `--volume N` — master volume override (0.0–1.0)

**`convert` flags:**
- `-o <file>` — specify output path
- `--project` — create a full `.ei` project with `parts/` directory

#### Playback

| Command | Aliases | What It Does | Examples |
|---------|---------|-------------|----------|
| `play` | — | Play any file (compiles first if needed) | `play song.mid`, `play song.e`, `play album.enx` |
| `gui` | `glass` | Play in glassmorphism GUI window | `gui song.mid`, `gui symphony.ei` |

`play` handles: `.e`, `.ei`, `.eci`, `.enx`, `.eic`, `.ec`, `.mid`, `.wav`, `.mp3`, `.mp4`

#### File Information

| Command | Aliases | What It Does | Examples |
|---------|---------|-------------|----------|
| `info` | `stats` | Show file statistics (events, BPM, duration, note range) | `info Rush_E.e`, `info project.ei` |

**Output example:**
```
E ...> info Rush_E.e
File: Rush_E.e
Events: 19853
BPM: 270.0
Duration: 174.23s
Note range: 21-108
```

#### Security & Signing

| Command | Aliases | What It Does | Examples |
|---------|---------|-------------|----------|
| `sign` | — | Sign a file with author name and social links | `sign song.eic`, `sign song.eic --embed` |
| `encrypt` | — | Encrypt a file to `.ee` (AES-256-GCM) | `encrypt song.e -o song.ee`, `encrypt project.ei -o bundle.ee` |

**`sign` flags:**
- `--embed` — embed signature inside the file (for `.eic`, `.ec`, `.ee`, `.ecc`)
- `--force` — overwrite existing signature

**Interactive signing:**
```
E ...> sign my_song.eic
Author> Tentari
Instagram> @tentari
Discord> pixelhollow
✓ Signed
```

#### Package Management

| Command | Aliases | Subcommands | What It Does | Examples |
|---------|---------|------------|-------------|----------|
| `mod` | — | `list`, `scan`, `update`, `fetch`, `remove`, `version`, `available` | Manage mods (safety-scanned Python extensions) | `mod list`, `mod scan`, `mod fetch cool-mod` |
| `plugin` | `plugins` | `list`, `scan`, `update`, `fetch`, `remove`, `version`, `available` | Manage plugins (Python extensions with full API) | `plugin list`, `plugin fetch visualizer` |
| `pkglist` | — | `show`, `update`, `search`, `version`, `detail` | Manage the remote package registry | `pkglist show`, `pkglist search rush` |
| `ezip` | — | `install`, `list`, `info` | Install and inspect EZip packages | `ezip install my_pack.ezip`, `ezip list bundle.ezip` |

**`mod` subcommand details:**
- `mod list` — show installed mods
- `mod scan` — security-scan all mods for dangerous patterns
- `mod update <name>` — update a specific mod from registry
- `mod fetch <name>` — download and install from registry
- `mod remove <name>` — uninstall
- `mod version` — show mod system version

**`plugin` subcommand details:**
- `plugin list` — show installed plugins
- `plugin scan` — security-scan all plugins
- `plugin update <name>` — update from registry
- `plugin fetch <name>` — download and install
- `plugin remove <name>` — uninstall
- `plugin version` — show plugin system version

**`pkglist` subcommand details:**
- `pkglist show` — display current registry URL
- `pkglist update url <http://...>` — change registry URL
- `pkglist search <term>` — search packages by name
- `pkglist version` — show package list version
- `pkglist detail <name>` — show detailed info about a package

**`ezip` subcommand details:**
- `ezip install <file.ezip>` — install a package
- `ezip list <file.ezip>` — show contents without installing
- `ezip info <file.ezip>` — show metadata

#### System Configuration

| Command | Aliases | Subcommands | What It Does | Examples |
|---------|---------|------------|-------------|----------|
| `audio` | — | `devices`, `set-device`, `config` | Configure audio output | `audio devices`, `audio set-device 2`, `audio config` |
| `gc` | — | `[strategy]` | View or change garbage collection strategy | `gc`, `gc aggressive`, `gc default` |

**`audio` subcommand details:**
- `audio devices` — list all audio output devices with driver type (WASAPI, DirectSound, MME, WDM-KS)
- `audio set-device N` — set active device by index number
- `audio config` — show current audio configuration (persisted to `audio_config.json`)

**`gc` strategy options:**
- `gc default` — deduplication, range check, zero-duration removal
- `gc aggressive` — also merges overlapping same-pitch notes
- `gc off` — disable GC (debugging only)

---

### Aliases — Shortcuts for Power Users

Every command has one or more aliases:

| You can type… | Same as… |
|---------------|----------|
| `chdir` | `cd` |
| `dir` | `ls` |
| `build` | `compile` |
| `glass` | `gui` |
| `stats` | `info` |
| `plugins` | `plugin` |
| `cls` | `clear` |
| `?` | `help` |
| `quit` | `exit` |

### Plugin Commands

Plugins (see section 45) can add their own commands to eshell. These appear automatically when the plugin is installed:

```
E ...> my_custom_command arg1 arg2
```

Plugin commands share the same prompt, error handling, and argument parsing as built-in commands. They can also override existing commands.

### Shell Features

#### Smart Path Handling

Eshell automatically strips quotes from paths, so you can copy-paste paths with spaces:

```
E ...> cd "C:\My Music\Project"
E ...> cd C:\My Music\Project       # Also works
```

#### Color Output

eshell automatically detects if your terminal supports color (ANSI escape codes). If it doesn't (e.g., redirecting to a file), colors are stripped.

#### Error Handling

Errors show in red with a clear message:

```
E ...> compile nonexistent.e -o out.mid
  ✗ Not found: nonexistent.e
```

Command errors are caught individually — the shell never crashes from a bad command.

#### Stopping Playback

Press `Ctrl+C` during playback to stop. Press `Ctrl+C` or `Ctrl+D` at the prompt to exit.

#### Plugin Auto-Loading

If a mod or plugin adds an `_eshell_commands` dictionary to `ep_core`, eshell loads those commands automatically at startup. You don't need to restart.

### Full eshell Workflow Example

A complete session from nothing to finished composition:

```powershell
# 1. Start eshell
py -3 eshell.py

# 2. See what's in the project
E ...> ls
  examples/  ep.py  eshell.py  player.py  ...

# 3. Check the example file
E ...> info examples/Rush_E.e
  19853 events, 270 BPM, 174s

# 4. Compile it to MIDI
E ...> compile examples/Rush_E.e -o rush.mid
  ✓ rush.mid (856KB)

# 5. Listen
E ...> play rush.mid

# 6. Convert to .eic to see the source
E ...> compile examples/Rush_E.e -o rush.eic
  ✓ rush.eic (462KB)

# 7. Sign it so people know it's yours
E ...> sign rush.eic
  Author> Your Name
  ✓ Signed

# 8. Done — exit
E ...> exit
  bye
```

---

## 4. #MACHINE Mode — The Precise Way

This is the original, exact, no-nonsense format. Every note is written as one line with absolute numbers.

### Anatomy of a Machine Line

```
T0    N60    D500    V0.8
│     │      │       └── Velocity (loudness: 0.0 = silent, 1.0 = max)
│     │      └────────── Duration in milliseconds (how long the note lasts)
│     └───────────────── MIDI note number (60 = C4, middle C)
└─────────────────────── Timestamp in milliseconds (when to start)
```

### A Real Example

```
@bpm 120
T0 N36 D500 V0.7      # Low bass note (C2)
T0 N60 D250 V0.8      # Middle C
T250 N64 D250 V0.8    # E4 — a third higher
T500 N67 D500 V0.85   # G4 — a fifth higher
```

This plays: **a C major chord** (C + E + G) with a bass note.

### Token Reference

| Token | Required | Range | Default | Meaning |
|-------|----------|-------|---------|---------|
| `T` | Yes | 0–9,999,999 | — | When to start the note (milliseconds) |
| `N` | Yes | 0–127 | — | Which piano key (MIDI note number) |
| `D` | No | 1–65535 | 500 | How long the note lasts (milliseconds) |
| `V` | No | 0.0–1.0 | 0.8 | How loud (0 = silent, 1 = max) |

### Tip for Beginners

```powershell
E ...> info myfile.e
```

This tells you: number of notes, BPM, total duration, and note range (lowest to highest).

---

## 5. #HUMAN Mode — The Readable Way

Instead of typing numbers, you write English-like commands. The computer figures out the rest.

### Single Note

```
play note(C4) @dur:q @vel:mf
```

This means: **Play C4 as a quarter note at mezzo-forte (medium-loud).**

Compare:
- **Machine:** `T0 N60 D500 V0.8`
- **Human:** `play note(C4) @dur:q @vel:mf`

Both produce the same sound. Human is easier to read; Machine is more precise.

### Duration Codes

| Code | Name | ms at 120 BPM |
|------|------|---------------|
| `w` | whole note | 2000ms (2 seconds) |
| `h` | half note | 1000ms (1 second) |
| `q` | quarter note | 500ms |
| `e` | eighth note | 250ms |
| `s` | sixteenth note | 125ms |
| `t` | thirty-second note | 62.5ms |

A dot after the code adds half again: `q.` = dotted quarter = 750ms.

### Velocity Codes (Loudness)

| Code | Italian Name | Meaning | Value |
|------|-------------|---------|-------|
| `ppp` | pianississimo | very very soft | 16 |
| `pp` | pianissimo | very soft | 33 |
| `p` | piano | soft | 49 |
| `mp` | mezzo-piano | medium-soft | 64 |
| `mf` | mezzo-forte | medium-loud | 80 |
| `f` | forte | loud | 96 |
| `ff` | fortissimo | very loud | 112 |
| `fff` | fortississimo | very very loud | 126 |

You can also use numbers: `@vel:80` is the same as `@vel:mf`.

### Properties Reference

| Property | Example | What It Does |
|----------|---------|-------------|
| `@dur:` | `@dur:q` | Duration (w/h/q/e/s/t + dotted) |
| `@vel:` | `@vel:mf` | Velocity / loudness |
| `@pan:` | `@pan:-0.5` | Stereo position (-1=left, 0=center, 1=right) |
| `@bend:` | `@bend:12` | Pitch bend in semitones |
| `@ch:` | `@ch:10` | MIDI channel (instrument) |

### Example

```
@bpm 120
play note(C3) @dur:h @vel:ff            # Loud low C for 1 second
play note(C4) @dur:q @vel:mf            # Medium middle C
play note(E4) @dur:e @vel:f             # Fast loud E
play note(G4) @dur:s @vel:pp            # Very soft fast G
```

---

## 6. File Formats at a Glance

| Extension | Name | What It Is | When to Use |
|-----------|------|-----------|-------------|
| `.e` | E Source | Raw composition (MACHINE or HUMAN) | **Writing music** — your main file |
| `.ei` | E Index | Project linking multiple `.e` files | **Multi-part songs** (verse, chorus, bridge) |
| `.eci` | E CI | Mixed MACHINE+HUMAN in one file | **Toggle between modes** with `@mode` |
| `.enx` | E NX | Root playlist ordering `.ei` files | **Albums** — play songs in sequence |
| `.eic` | E Clear | One-file bundle of entire project | **Sharing** — everything in one text file |
| `.ec` | E Compiled | Pre-parsed binary (fast) | **Large files** — no parsing needed |
| `.ee` | E Encrypted | AES-encrypted `.e` or bundle | **Secure distribution** — password needed |
| `.mid` | Standard MIDI | Universal music file | **Play anywhere** — DAWs, games, phones |
| `.wav` | Waveform | Uncompressed audio | **Highest quality** — for mastering |
| `.mp3` | MP3 | Compressed audio | **Small files** — sharing online |
| `.mp4` | MP4 Video | Piano roll visual + audio | **Social media** — video with sound |

---

## 7. Syntax Version Compatibility

E has evolved through five major syntax versions. This document covers **v5 (latest — the canonical default)**. v5 = v4 + piano performance features (sustain pedal, rests, articulations, tuplets, octave shift, velocity curves, ties). v1-v4 still compile but are deprecated and emit warnings.

### Version Table

| Version | Status | Key Features | When to Use |
|---------|--------|-------------|-------------|
| **v1 #MACHINE** | ✅ Supported | `T{N} N{N} D{N} V{N}` token stream | Precision timing, AI generation, large files |
| **v1 #HUMAN** | ✅ Supported | `play note(C4) @dur:q @vel:mf` | Readable compositions, teaching |
| **v2 Semantic** | ⚠️ Deprecated | `[Section:]`, chord blocks, scale degrees | Existing v2 projects (migrate to v5) |
| **v3 Shorthand** | ✅ Supported | `C4 q`, macros `!name`, repeats `xN`, probability `?0.8` | Quick prototyping, concise notation |
| **v4 Polyrhythm** | ✅ Latest | `[notes]/N`, Euclidean `E(N,M)`, scale quantization, polyrhythms `(X:Y)` | Complex rhythms, modern compositions |
| **v4 .eci** | ⚠️ Deprecated | `@mode machine/human/auto` toggle within one file | Mixed-precision files |
| **v4 .ei** | ⚠️ Deprecated | Project index with `include`, `section`, `play`, `root` inheritance | Multi-part songs, orchestral works |
| **v4 .enx** | ⚠️ Deprecated | Album ordering with `order`, tempo override, delays | Albums, concerts, practice loops |

### What's Deprecated in v4

| Feature | v2 / Old Way | v4 Replacement |
|---------|-------------|----------------|
| `[Section: name]` header | Old v2 block syntax | `section "Name" { ... }` in `.ei` or `.eci` |
| `{Chord_Block: N_bars}` | v2 chord block | Write chords as simultaneous `T{N}` lines or use `.ei` project structure |
| `Key: X` directive | v2-style header | `@key X` directive (works everywhere) |
| `Tempo: N` in v2 headers | v2-style | `@bpm N` or `tempo N` in `.ei` |
| `Time: 4/4` | v2 time signature | Not yet supported in v4 (defaults to 4/4) |
| Standalone `.e` only | Single-file compositions | `.ei` projects for anything complex |

### v2 → v4 Migration Guide

If you have old v2 `.e` files, here's how to update them:

**v2 (old):**
```
[Section: I. Adagio]
  Key: C#_minor
  Tempo: 55

  {Chord_Block: 4_bars}
    C#_minor | A_Major
  {End}

  {Melody_Block}
    arpeggio(up, dur=sixteenth, vel=pp)
  {End}
{End}
```

**v4 (migrated):**
```
@key C#_minor
@bpm 55

section "I. Adagio" {
    // Chord block equivalent: simultaneous notes
    T0 N49 D2000 V0.7     // C#3
    T0 N56 D2000 V0.7     // G#3
    T0 N61 D2000 V0.7     // C#4

    // Arpeggio equivalent
    T0 N49 D125 V0.5
    T125 N56 D125 V0.5
    T250 N61 D125 V0.5
    T375 N68 D125 V0.5
}
```

### v3 Features That Carry Forward

All v3 shorthand works in v4:

| v3 Feature | Example | Works in v4? |
|------------|---------|--------------|
| Note shorthand | `C4 q` | ✅ Yes |
| Tempo aliases | `@adagio` | ✅ Yes |
| Macros | `!bass = T0 N36 D500` | ✅ Yes |
| Repeats | `x4` suffix | ✅ Yes |
| Probability | `?0.8 T{N}` | ✅ Yes |
| Randomization | `V~0.2`, `D~30`, `N60-72` | ✅ Yes |
| Parallel `&` | `T0 N60 & T0 N64` | ✅ Yes |
| Block comments | `/* ... */` | ✅ Yes |
| Tempo curves | `@bpm 60->180` | ✅ Yes |
| Roman numerals | `chord(I)` | ✅ Yes |
| Dynamic arcs | `ppp < ff > pp` | ✅ Yes |
| Articulation | `C4 q staccato` | ✅ Yes |

### Detecting Which Version a File Uses

The compiler auto-detects:

| Pattern in File | Detected As |
|----------------|-------------|
| `T{N} N{N}` at line start | v1 #MACHINE |
| `play note(` or `play chord(` | v1 #HUMAN |
| `[Section:` or `play(` or `arpeggio(` | v2 Semantic |
| `C4 q`, `!name =`, `?0.8` | v3 Shorthand |
| `[notes]/N`, `E(N,M)`, `@mode` | v4 |

You can force the version with `@mode machine`, `@mode human`, or `@mode auto` (see section 31).

---

## 8. Notes, Chords, and Scales — Music Theory for E

### Note Names

On a piano keyboard, notes are named A through G:

```
  C#4  D#4        F#4  G#4  A#4        C#5
C4    D4    E4    F4    G4    A4    B4    C5
```

The number tells you which octave. C4 is middle C. C5 is one octave higher.

In E, you write:
- `C4` = middle C
- `D#4` = D sharp, the black key between D and E
- `Bb3` = B flat, the black key between A and B

Wait, what about `#` (sharp) and `b` (flat)?
- **Sharp (#)** = one key higher. C# is the black key right after C.
- **Flat (b)** = one key lower. Db is the same black key as C#.

Same black key, two names. E accepts both `C#4` and `Db4`.

### What Are Chords?

A chord is multiple notes played at the same time. A **C major chord** is:
- C (the root)
- E (the third — 4 semitones above C)
- G (the fifth — 7 semitones above C)

Together they sound "happy." A **C minor chord** is:
- C (root)
- Eb (minor third — 3 semitones above C)
- G (fifth)

Together they sound "sad."

### What Are Scales?

A scale is a set of notes that sound good together. **C major** uses only the white keys:

```
C D E F G A B C  (8 notes, then repeats)
```

**A minor** also uses only white keys:

```
A B C D E F G A  (sounds sadder)
```

E has built-in scale quantization (see section 22). You tell it what scale you're in, and it snaps wrong notes to the right ones automatically.

---

## 9. Durations & Rhythm

### In #MACHINE Mode

Duration is in milliseconds. At 120 BPM (beats per minute), one beat = 500ms.

```
T0 N60 D500 V0.8     # Quarter note (1 beat = 500ms)
T500 N60 D250 V0.8   # Eighth note (half a beat = 250ms)
T750 N60 D125 V0.8   # Sixteenth note (quarter beat = 125ms)
```

### Timing Reference Table

At BPM `b`: one beat = `60000 / b` milliseconds.

| BPM | Quarter (1 beat) | Eighth (½) | Sixteenth (¼) | 32nd (⅛) |
|-----|-----------------|------------|---------------|----------|
| 60 | 1000ms | 500ms | 250ms | 125ms |
| 120 | 500ms | 250ms | 125ms | 62.5ms |
| 180 | 333ms | 167ms | 83ms | 42ms |
| 240 | 250ms | 125ms | 62.5ms | 31ms |

### In #HUMAN Mode

You use letter codes: `w` (whole), `h` (half), `q` (quarter), `e` (eighth), `s` (sixteenth), `t` (32nd).

```
play note(C4) @dur:w      # Whole note — 4 beats
play note(C4) @dur:h      # Half note — 2 beats
play note(C4) @dur:q      # Quarter note — 1 beat
play note(C4) @dur:e      # Eighth note — ½ beat
play note(C4) @dur:s      # Sixteenth note — ¼ beat
play note(C4) @dur:q.     # Dotted quarter — 1½ beats
```

### Putting It Together — A Simple Melody

```
@bpm 120
play note(C4) @dur:q @vel:mf
play note(D4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(F4) @dur:q @vel:mf
play note(G4) @dur:h @vel:ff
```

This plays: C - D - E - F - G (the first five notes of a major scale), each one beat, ending with a loud two-beat G. That's "Twinkle Twinkle Little Star" if you go back down.

---

## 10. Velocity & Dynamics (Loud or Soft)

### What Is Velocity?

Velocity is how hard you press a piano key. Harder = louder. E uses 0–127, where 0 is silent and 127 is maximum.

### In #MACHINE Mode

```
V0.1    # Barely audible
V0.3    # Soft
V0.5    # Medium
V0.8    # Loud (default)
V1.0    # Maximum
```

The number is a fraction of 127. `V0.8` = velocity 101.

### In #HUMAN Mode

```
play note(C4) @vel:ppp      # Extremely soft (16)
play note(C4) @vel:p        # Soft (49)
play note(C4) @vel:mp       # Medium-soft (64)
play note(C4) @vel:mf       # Medium-loud (80) — default
play note(C4) @vel:f        # Loud (96)
play note(C4) @vel:ff       # Very loud (112)
play note(C4) @vel:fff      # Maximum (126)
```

### Dynamic Contrast — The Secret to Good Music

Real music isn't all the same volume. Changes in loudness create emotion.

```
play note(C4) @dur:h @vel:pp      # Start soft
play note(E4) @dur:q @vel:mp      # Get a little louder
play note(G4) @dur:q @vel:mf      # Medium
play note(C5) @dur:h @vel:ff      # End loud!
```

This is called a **crescendo** — getting gradually louder.

---

## 11. Multiple Notes at Once — Chords

### In #MACHINE Mode

Put the same timestamp on multiple lines:

```
T0 N36 D1000 V0.7    # Bass C2
T0 N48 D1000 V0.8    # C3
T0 N60 D1000 V0.8    # C4 (middle C)
T0 N64 D1000 V0.8    # E4
T0 N67 D1000 V0.8    # G4
```

All five lines start at T0 = all five notes play simultaneously = **C major chord** with full voicing.

### In #HUMAN Mode

```
play chord(C, major) @dur:h @vel:ff
play chord(D, minor) @dur:q @vel:mf
play chord(G, dom7) @dur:h @vel:f
play chord(C, major) @dur:w @vel:fff
```

### Supported Chord Qualities

| Name | Example | Sounds Like |
|------|---------|-------------|
| `major` | `C, major` | Happy, bright |
| `minor` | `D, minor` | Sad, dark |
| `dom7` | `G, dom7` | Tense, wants to resolve |
| `min7` | `A, min7` | Jazzy, relaxed |
| `dim` | `B, dim` | Scary, unstable |
| `sus4` | `C, sus4` | Suspended, airy |
| `aug` | `C, aug` | Dreamy, floating |

### Strumming (Guitar-like)

```
play chord(C, major) @dur:h @strum:down(15ms)
play chord(G, major) @dur:q @strum:up(20ms)
play chord(A, minor) @dur:h @strum:random(10ms)
```

Strumming plays each note of the chord slightly after the previous one, like a guitar strum.

---

## 12. MIDI Note Reference (Piano Key Map)

Here is every note on a standard 88-key piano:

```
C0=12  C1=24  C2=36  C3=48  C4=60  C5=72  C6=84  C7=96   C8=108
C#0=13 C#1=25 C#2=37 C#3=49 C#4=61 C#5=73 C#6=85 C#7=97
D0=14  D1=26  D2=38  D3=50  D4=62  D5=74  D6=86  D7=98
D#0=15 D#1=27 D#2=39 D#3=51 D#4=63 D#5=75 D#6=87 D#7=99
E0=16  E1=28  E2=40  E3=52  E4=64  E5=76  E6=88  E7=100
F0=17  F1=29  F2=41  F3=53  F4=65  F5=77  F6=89  F7=101
F#0=18 F#1=30 F#2=42 F#3=54 F#4=66 F#5=78 F#6=90 F#7=102
G0=19  G1=31  G2=43  G3=55  G4=67  G5=79  G6=91  G7=103
G#0=20 G#1=32 G#2=44 G#3=56 G#4=68 G#5=80 G#6=92 G#7=104
A0=21  A1=33  A2=45  A3=57  A4=69  A5=81  A6=93  A7=105
A#0=22 A#1=34 A#2=46 A#3=58 A#4=70 A#5=82 A#6=94 A#7=106
B0=23  B1=35  B2=47  B3=59  B4=71  B5=83  B6=95  B7=107
```

### Quick Formula

```
MIDI number = semitone + (octave + 1) × 12

Where semitone: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11

Example: C4 = 0 + (4+1)×12 = 0 + 60 = 60
Example: A4 = 9 + (4+1)×12 = 9 + 60 = 69  (this is 440Hz, standard tuning)
```

### Piano Ranges

| Range | MIDI | Keyboard Section |
|-------|------|-----------------|
| 0–23 | C0 to B0 | Sub-contra (very deep, felt more than heard) |
| 24–47 | C1 to B1 | Bass (left hand) |
| 48–71 | C3 to B3 | Mid-range (C4 = middle C = 60) |
| 72–95 | C5 to B5 | Upper (right hand melody) |
| 96–127 | C7 to G9 | High (glittering top notes) |

---

## 13. BPM & Tempo

BPM = Beats Per Minute. It controls how fast the music plays.

- **60 BPM** = 1 beat per second (slow, like a ballad)
- **120 BPM** = 2 beats per second (moderate, walking pace)
- **180 BPM** = 3 beats per second (fast, like Rush E)
- **240 BPM** = 4 beats per second (extremely fast)

### Setting Tempo

```
@bpm 120
```

Or the old-style:

```
@tempo 120
```

### How BPM Affects Duration

At 120 BPM, one quarter note = 500ms. At 240 BPM, one quarter note = 250ms. Everything gets faster.

---

## 14. Tempo Aliases (Italian Words)

Classical music uses Italian words for tempo. E supports them:

```
@adagio          # 56 BPM — slow and stately
@andante         # 76 BPM — walking pace
@moderato        # 100 BPM — moderate
@allegro         # 120 BPM — fast, cheerful
@vivace          # 140 BPM — lively
@presto          # 180 BPM — very fast
@prestissimo     # 210 BPM — extremely fast
```

Full list:

| Alias | BPM | Mood |
|-------|-----|------|
| `@larghissimo` | 20 | Extremely slow, broad |
| `@grave` | 40 | Very slow, solemn |
| `@largo` | 50 | Slow, spacious |
| `@lento` | 55 | Slow |
| `@adagio` | 56 | Slow, stately |
| `@adagietto` | 65 | Slightly faster than adagio |
| `@andante` | 76 | Walking pace |
| `@andantino` | 85 | Slightly faster than andante |
| `@moderato` | 100 | Moderate |
| `@allegretto` | 110 | Moderately fast |
| `@allegro` | 120 | Fast, cheerful |
| `@vivace` | 140 | Lively |
| `@presto` | 180 | Very fast |
| `@prestissimo` | 210 | Extremely fast |

---

## 15. Comments (Document Your Music)

Comments are notes to yourself (or others) that the computer ignores. E supports **three comment styles** that work in **all parsers** (`.e`, `.ei`, `.eci`, `.enx`).

### Single-Line `//`

Anything after `//` on a line is ignored. Works everywhere.

```
// This entire line is a comment
T0 N60 D500 V0.8   // This is the melody note
play note(C4) @dur:q  // Human mode also supports it
order "song.ei" tempo 120  // Works in .enx too
include "parts/bass.e" as bass  // Works in .ei too
```

### Block Comments `/* */`

Block comments can span multiple lines. They are **stripped before parsing**, so they work in all syntax modes — not just v3.

```
T0 N36 D500 V0.7
/* This entire block is a comment.
   It can span multiple lines.
   It's removed before the parser sees the file. */
T500 N43 D500 V0.7
```

You can also use them inline:
```
T0 N60 /* this is ignored */ D500 V0.8
```

### The `#` Comment (Legacy)

Lines starting with `#` are also treated as comments in `.e` files. However, `#` is also used for `#ENX`, `#MACHINE`, and `#compiler` directives — use `//` for new code.

```
# This line is ignored (legacy)
// This line is also ignored (preferred)
```

### Why Use Comments?

- Explain what a section does
- Mark the key or chord changes
- Leave yourself reminders
- Help others understand your music
- Temporarily disable a line without deleting it

### Technical Note: Comment Stripping

E uses a **centralized comment stripper** (`ep_compiler/comments.py`) that removes all comments **before** parsing begins. This means:
- `/* */` block comments work in ALL parsers (`.e`, `.ei`, `.eci`, `.enx`)
- Nested block comments are handled correctly
- Comments inside strings are preserved (not stripped)
- The stripper runs before syntax detection, so comments never interfere with format detection

---

## 16. v2 Semantic Syntax — Think in Music, Not Numbers

v2 is a higher-level way to compose. You describe **chords, arpeggios, and patterns** instead of individual notes. The computer fills in the details.

### Basic Structure

```
[Section: My Section Name]
  Key: C_Major
  Tempo: 120
  Time: 4/4

  {Chord_Block: 4_bars}
    C_Major | D_minor | G_dom7 | C_Major
  {End}

  {Melody_Block}
    arpeggio(up, dur=sixteenth, vel=mp)
    play(third, dur=half, vel=f)
    play(fifth, dur=quarter, vel=mf)
  {End}
{End}
```

### Section Header

```
[Section: I. The Awakening]
  Key: C#_minor       # Which key you're in
  Tempo: 55            # How fast
  Time: 4/4            # Time signature (4 beats per bar)
```

### Chord Blocks

Write chord names separated by `|`. Each chord lasts one bar.

```
{Chord_Block: 4_bars}
  C_Major | D_minor | G_dom7 | C_Major
{End}
```

Available chord types: `C_Major`, `A_minor`, `G_dom7`, `D_min7`, `Fdim`, `Bb_Major`, etc.

### Melody Block Commands

| Command | What It Does |
|---------|-------------|
| `play(root, dur=quarter, vel=mf)` | Play the root note of the current chord |
| `play(third, dur=eighth, octave=up)` | Play the third, an octave higher |
| `play(fifth, dur=half, vel=ff)` | Play the fifth, loud |
| `arpeggio(up, dur=sixteenth, vel=f)` | Roll chord notes up (ascending) |
| `arpeggio(down, dur=sixteenth)` | Roll chord notes down (descending) |
| `arpeggio(random, dur=sixteenth)` | Roll in random order |
| `chromatic_run(up, 2_octaves, dur=16th, vel=ff)` | Run up all notes in 2 octaves |
| `chromatic_run(down, 3_octaves, dur=32nd)` | Run down |
| `glissando(from=C4, to=C6, dur=half)` | Slide between two notes |
| `hold(half)` | Wait for the duration (silence) |

### Scale Degrees

| Degree | What It Means |
|--------|--------------|
| `root` | The base note of the chord (e.g., C in C major) |
| `third` | The note that makes it major or minor |
| `fifth` | The perfect fifth |
| `seventh` | Adds tension (dom7) |
| `octave` | Root one octave higher |

### Full Example — Like Moonlight Sonata

```
[Section: I. Adagio Sostenuto]
  Key: C#_minor
  Tempo: 55
  Time: 4/4

  {Chord_Block: 16_bars}
    C#_minor | C#_minor | C#_minor | C#_minor
    A_Major  | A_Major  | F#_minor | G#_dom7
    C#_minor | C#_minor | A_Major  | F#_minor
    G#_dom7  | G#_dom7  | C#_minor | C#_minor
  {End}

  {Melody_Block}
    arpeggio(up, dur=triplet_eighth, vel=pp)
    arpeggio(up, dur=triplet_eighth, vel=pp)
    play(third, dur=half, vel=mp)
    arpeggio(up, dur=triplet_eighth, vel=pp)
    play(fifth, dur=half, vel=mp)
  {End}
{End}
```

**The secret:** Constant triplet motion, sparse melody over rich arpeggios, slow chord changes (one chord per 4 bars), dynamic arc from very soft to medium to soft again.

---

## 17. v3 Shorthand — Fast & Friendly

v3 is for when you want to write music quickly. It combines the best of MACHINE and HUMAN.

### Note Shorthand

Instead of writing `play note(C4) @dur:q`, just write:

```
C4 q             # C4 as a quarter note
D#5 e            # D#5 as an eighth note
E4 h staccato    # E4 half note, staccato
F4 q ff          # F4 quarter note, fortissimo
```

### Pattern: Note + Duration + Optional Velocity

```
C4 q mf          # Note  Duration  Velocity
```

It's that simple. The computer assumes `@bpm 120` if you don't set one.

### Repeat Suffix

```
T0 N60 D500 V0.8 x4     # Play this note 4 times, spaced 1000ms apart
C4 q x2                  # Play C4 quarter note twice
```

### Block Comments

```
/* This is a block comment
   It can go across multiple lines */
T0 N60 D500
```

---

## 18. Macros — Reuse Patterns

If you use the same pattern multiple times, define it once with a `!name` (macro).

### Define a Macro

```
!bass = T0 N36 D500 V0.7 T500 N43 D500 V0.7
```

Now `!bass` expands to those two notes everywhere you use it.

### Use a Macro

```
!bass                    # Plays the bass pattern
T0 N60 D500 V0.8         # Melody note
!bass                    # Bass pattern again
```

### Macros in #HUMAN Mode

```
!melody = C4 q E4 q G4 q
play note(C4) @dur:h     # Intro note
!melody                  # Expands to C4 E4 G4
!melody                  # Again
```

### Macro with Repeats

```
!riff = T0 N60 D250 V0.8 T250 N64 D250 V0.8 T500 N67 D250 V0.8
!riff x4                 # Repeats the riff 4 times
```

---

## 19. Repeats — Play It Again

You can repeat any line using `xN` where N is the number of times.

```
T0 N60 D500 V0.8 x3      # Plays 3 times: T0, T1000, T2000
```

The gap between repeats is the duration of the original note (or the difference to the next note in the same line).

```
C4 q x3                   # Play C4 quarter note 3 times
```

---

## 20. Probability & Randomization — Add Surprise

### Probability Gates

Make a note play only some of the time:

```
?0.8 T1000 N64 D250 V0.9    # 80% chance this note plays
?0.3 T2000 N60              # 30% chance (rare)
?1.0 T0 N72                 # 100% chance (always plays)
```

### Randomization

Add `~` after a value to randomize it:

```
T0 N60 D500 V~0.2        # Velocity: 0.6 to 1.0 (±0.2)
T0 N60 D~30 V0.8         # Duration: ±30ms random
T0 N~12 D500 V0.8        # Note: ±12 semitones random
```

### Range Notation

Pick a random note between two values:

```
T0 N60-72 D500 V0.8      # Random MIDI note between 60 and 72
T500 N64-76 D250 V0.9    # Random note in range
```

---

## 21. Parallel Notation — Chords on One Line

Use `&` to play multiple notes at the same time:

```
T0 N60 & T0 N64 & T0 N67     # C major chord (3 notes, same timestamp)
T500 N36 & T500 N60 & T500 N64  # Bass + chord
```

This is a shorter way to write a chord than three separate lines.

---

## 22. Key Modulation — Change Key Mid-Song

Use `@key` to set the musical key. This affects how chords are interpreted.

```
@key C major
T0 N60 D500 V0.8    # C — sounds like "home"
T0 N64 D500 V0.8    # E — the major third
T0 N67 D500 V0.8    # G — the dominant

@key G major        # Modulate to a new key
T0 N67 D500 V0.8    # Now G feels like "home"
T0 N71 D500 V0.8    # B — the major third in G
```

### Supported Keys

```
C_Major, G_Major, D_Major, A_Major, E_Major, F_Major, Bb_Major
A_minor, D_minor, E_minor, C#_minor, F#_minor, G_minor
```

### Why Change Key?

Modulation creates emotional impact. Moving from a minor key to a major key feels like "sun coming out." Moving up by a semitone creates tension and excitement (common in pop music).

---

## 23. Scale Quantization — Snap Notes to a Scale

Set a scale, and any notes outside it will automatically snap to the nearest correct note.

```
@scale C_Major
T0 N61 D500 V0.8    # C# — outside C major, snaps to C (60) or D (62)
T0 N66 D500 V0.8    # F# — outside, snaps to F (65) or G (67)
```

This is useful when:
- You generated random notes and want them to sound good
- You imported a MIDI file and want to force it into a scale
- You're experimenting and want a safety net

Turn it off with `@scale off`.

### How It Works

E builds a **lookup table** for each scale — for every one of the 12 semitones, it pre-computes the nearest in-scale note. This makes quantization O(1) per note regardless of scale size.

### Performance: NumPy Vectorized

For large compositions (10,000+ events), scale quantization uses **NumPy vectorization** to process all notes in a single array operation instead of a Python loop:

| Batch Size | Before (loop) | After (vectorized) |
|------------|---------------|-------------------|
| 100 notes | ~0.5ms | ~0.05ms |
| 10,000 notes | ~50ms | ~0.5ms |
| 100,000 notes | ~500ms | ~5ms |

For small batches (< 50 notes), it automatically falls back to the simple loop (avoids NumPy overhead).

### Supported Scales

Major scales: `C_Major`, `G_Major`, `D_Major`, `A_Major`, `E_Major`, `F_Major`, `Bb_Major`, `Db_Major`
Minor scales: `A_minor`, `D_minor`, `E_minor`, `C#_minor`, `F#_minor`, `G_minor`, `C_minor`, `F_minor`

---

## 24. Channel Binding — Multiple Instruments

MIDI has 16 channels (0–15). Each channel can be a different instrument (piano, violin, drums, etc.).

### In #MACHINE Mode

```
CH[10] T0 N36 D500 V0.7    # Channel 10 = drums
CH[1] T0 N60 D500 V0.8     # Channel 1 = piano
CH[2] T0 N64 D500 V0.8     # Channel 2 = strings
```

### In #HUMAN Mode

```
play note(C4) @dur:q @vel:mf @ch:5     # Channel 5
play note(C4) @dur:q @vel:mf @ch:10    # Channel 10 (drums)
```

### Track Names

```
CH[1] TRK[bass] T0 N36 D500 V0.7     # Label the track
CH[10] TRK[drums] T0 N42 D250 V0.9
```

### MIDI Instrument Map (Quick)

| Channel | Typical Instrument | Program Number |
|---------|-------------------|----------------|
| 0 | Acoustic Grand Piano | 0 |
| 1 | Electric Piano | 4 |
| 2 | Organ | 16 |
| 3 | Violin | 40 |
| 4 | Cello | 42 |
| 5 | Trumpet | 56 |
| 6 | Saxophone | 65 |
| 7 | Flute | 73 |
| 9 | Guitar | 24 |
| 10 | Drums (percussion) | — (special) |

Channel 10 is special — it's drums. Each MIDI note is a different drum sound (36=kick, 38=snare, 42=hi-hat).

---

## 25. Tempo Curves — Speed Up / Slow Down

Make the music accelerate or decelerate over time.

```
@bpm 60->180             # Start slow (60), end fast (180) — accelerando
@bpm 140->80             # Start fast (140), end slow (80) — ritardando
```

### Music Theory Terms

- **Accelerando** = speed up gradually
- **Ritardando** = slow down gradually
- **Rallentando** = slow down and broaden

---

## 26. Polyrhythms & Euclidean Rhythms

Advanced rhythm patterns that create complex, interlocking grooves.

### Triplets (3 notes in the space of 1 beat)

```
[C4 D4 E4]/3         # Three notes equally spaced over one beat
```

### Nested Polyrhythm

```
[C4 D4 E4 F4]/5      # Five notes over one beat (quintuplet)
```

### Euclidean Rhythm

```
E(5,4)               # 5 pulses spread over 4 beats — a "limping" rhythm
E(7,8)               # 7 over 8 — Cuban clave pattern
E(3,2)               # 3 over 2 — hemiola
```

Euclidean rhythms distribute N pulses as evenly as possible across M steps. They're named after the Euclidean algorithm and appear in African, Cuban, and Balkan music.

### Manual Polyrhythm Ratio

```
[notes in brackets] (X:Y)    # X notes over Y beats
[C4 D4 E4] (5:4)            # 5 notes over 4 beats
[C4 D4] (3:2)               # 3 notes over 2 beats (hemiola)
```

### Ritardando within a Polyrhythm

```
ritard(2 bars) -> 70         # Over 2 bars, gradually slow to 70 BPM
```

---

## 27. Macro Transposition — Shift Notes Up/Down

Shift an entire pattern by `N` semitones.

```
!pattern = N60 N64 N67 N72
!pattern[+12]        # Transpose up one octave: N72 N76 N79 N84
!pattern[-5]         # Transpose down a perfect 4th: N55 N59 N62 N67
!pattern[inv]        # Invert the intervals: N60 N56 N53 N48
```

### Conditional Macros

```
!macro^       # Only use this macro version if the previous condition is met
!macro_inv    # Inverted version of a macro
```

---

## 28. Dynamic Arcs — Get Louder Then Softer

```
ppp < ff > pp            # Start barely audible, crescendo to max, then back down
mp < fff > p             # Medium-soft, build to max, drop to soft
```

E translates these into velocity changes across your notes.

---

## 29. Articulation — Staccato / Legato / Accent

Articulation changes how a note is played:

```
C4 q staccato            # Short and detached (30% of full duration)
C4 q legato              # Smooth and connected (95% of full duration)
C4 q tenuto              # Held to full length
C4 q accent              # Emphasized attack (louder start)
```

---

## 30. Roman Numeral Chords — I–IV–V–vi

Use Roman numerals to refer to chords in the current key.

```
@key C major
chord(I)                 # C Major
chord(IV)                # F Major
chord(V)                 # G Major
chord(vi)                # A Minor
```

### Roman Numeral Reference (in C major)

| Numeral | Chord | Function |
|---------|-------|----------|
| I | C Major | Tonic (home) |
| ii | D Minor | Supertonic |
| iii | E Minor | Mediant |
| IV | F Major | Subdominant |
| V | G Major | Dominant (creates tension) |
| vi | A Minor | Relative minor |
| vii° | B Dim | Leading tone (very tense) |

The most common progression: **I–V–vi–IV** (used in thousands of pop songs).

---

## 31. .ei Project Index — Multi-File Songs

When a song gets complex, split it into multiple `.e` files and link them with an `.ei` index.

### Example Structure

```
my_symphony/
├── index.ei              # The project file
├── parts/
│   ├── opening.e         # Each instrument/movement in its own file
│   ├── development.e
│   └── coda.e
```

### index.ei

```
project "Symphony No. 1"
composer "AI"
tempo 120

include "parts/opening.e" as opening
include "parts/development.e" as dev
include "parts/coda.e" as coda

section "I. Opening" {
    play opening
}
section "II. Development" {
    tempo 90
    play dev after 1000ms
}
section "III. Finale" {
    tempo 140
    play opening with coda      // Play both simultaneously
}
```

### .ei Directives

| Directive | What It Does |
|-----------|-------------|
| `project "..."` | Name of the composition |
| `composer "..."` | Your name (or AI name) |
| `tempo N` | Default BPM |
| `include "path" as name` | Load a `.e` file and call it `name` |
| `include_dir "path/" as name` | Load all `.e` files in a directory |
| `section "Name" { ... }` | Define a section with commands inside |
| `play name` | Play the included file's content |
| `play name after Nms` | Play it after a delay |
| `play A with B` | Play two parts simultaneously |
| `wait Nms` | Insert silence |
| `tempo N` | Override BPM for this section (inside section block) |

### Real .ei Example — 3-Movement Sonata

```
project "Sonata in A Minor"
composer "Tentari"
tempo 120

// ── Part declarations ──
include "parts/bass.e" as bass
include "parts/melody.e" as melody
include "parts/arpeggios.e" as arp
include "parts/percussion.e" as drums
include_dir "cues/" as cues

// ── Movement I: Allegro ──
section "I. Allegro" {
    tempo 140
    play bass
    play melody after 2000ms
    play arp with melody
}

// ── Movement II: Adagio ──
section "II. Adagio" {
    tempo 55
    play arp
    play melody after 4000ms
    wait 2000ms
    play bass with melody
}

// ── Movement III: Presto ──
section "III. Presto" {
    tempo 180
    play drums
    play bass after 1000ms
    play melody with arp
}
```

### Using `include_dir`

If you have many files in a folder, include them all at once:

```
include_dir "motifs/" as library

section "Development" {
    play library/motif_a
    play library/motif_b after 500ms
    play library/motif_c with library/motif_d
}
```

Each `.e` file in the folder gets prefixed with the name you gave.

### Compile a Project

```powershell
E ...> compile my_symphony/index.ei -o symphony.mid
```

### Inline Sections

You can write sections on one line:

```
section "Main" { play opening }
section "Verse" { play dev after 500ms }
section "Bridge" { tempo 90; play dev with bass; wait 1000ms; play coda }
```

### .ei Directory Structure Best Practices

```
project_root/
├── index.ei                    # Main project file
├── parts/                      # Individual instrument/movement files
│   ├── bass.e
│   ├── melody.e
│   ├── harmony.e
│   └── percussion.e
├── cues/                       # Short cue files (for include_dir)
│   ├── intro.e
│   ├── bridge.e
│   └── finale.e
├── sections/                   # Sub-sections for large works
│   ├── exposition.ei
│   └── recapitulation.ei
└── project.enx                 # Root index (see section 32)
```

---

## 32. .eci Mode-Toggle Files — One File, Both Syntaxes

`.eci` files let you switch between #MACHINE and #HUMAN syntax mid-file using `@mode`.

```
@mode machine
T0 N36 D500 V0.7
T0 N60 D250 V0.8
@mode human
play note(C4) @dur:q @vel:mf
play note(G4) @dur:h @vel:ff
@mode auto
T500 N64 D250 V0.8
C5 q
```

### Full .eci Example — Bass in Machine, Melody in Human

This is the most common pattern: machine for precise rhythm and chords, human for readable melody:

```
@mode machine
// Bass line — exact timings needed
T0 N36 D1000 V0.7
T1000 N43 D500 V0.6
T1500 N48 D500 V0.7
T2000 N36 D1000 V0.7
T3000 N43 D500 V0.6
T3500 N48 D500 V0.7

@mode human
// Melody — easier to read as note names
play note(C4) @dur:q @vel:mf
play note(E4) @dur:e @vel:f
play note(G4) @dur:e @vel:f
play note(C5) @dur:h @vel:ff
play note(B4) @dur:e @vel:mf
play note(G4) @dur:e @vel:mf
play note(E4) @dur:q @vel:p
play note(D4) @dur:q @vel:mp
play note(C4) @dur:w @vel:pp

@mode auto
// This section is auto-detected
T4000 N60 D250 V0.9     // Machine detects the T/N pattern
C5 q mf                  // Human detects the note+duration pattern
```

### Mode Options

| Directive | Behavior |
|-----------|----------|
| `@mode machine` | Every line parsed as #MACHINE tokens |
| `@mode human` | Every line parsed as #HUMAN play commands |
| `@mode auto` | Signature-based auto-detection (see below) |
| `@mode strict` | Fail immediately on unparseable lines |

### `@mode auto` — How It Works

Instead of blindly trying machine-first-then-human (which could cause misclassification), `@mode auto` uses **signature-based routing**:

| Line Starts With | Routed To |
|-----------------|-----------|
| `T` followed by a digit | #MACHINE parser |
| `play ` | #HUMAN parser |
| Note name + duration (e.g. `C4 q`, `D#5 e`) | v3 shorthand parser |
| `!` at start | Macro definition |
| `?` followed by a number | Probability gate |
| Anything else | #MACHINE first, then #HUMAN fallback |

This prevents a v3 shorthand line like `C4 q mf` from being mistakenly parsed as a MACHINE token (which would produce timing drift).

If 10+ consecutive lines fail to parse under `@mode auto`, a warning is printed:
```
[eci] warning: 10 consecutive unparseable lines under @mode auto
```

### `@mode strict` — Fail-Fast Validation

`@mode strict` is for debugging and quality control. If any line doesn't parse cleanly as either MACHINE or HUMAN, compilation **stops immediately** with an error:

```
@mode strict
T0 N60 D500          # OK — parses as machine
this is not syntax   # ERROR: Strict mode: unparseable line 'this is not syntax'
```

Use strict mode when:
- You're converting a file from one format to another and want to catch every invalid line
- You're writing a linter or validator
- You want to guarantee zero silent parsing errors in your output

### Switching Modes for Different Sections

You can toggle modes as many times as you want, even within the same section:

```
@mode machine
T0 N36 D500 V0.7
T500 N43 D500 V0.7

@mode human
play chord(C, major) @dur:h @vel:ff       // Human chord
play chord(G, dom7) @dur:q @vel:f

@mode strict
T1500 N60 D250 V0.9                        // Strict: must parse cleanly
T1750 N64 D250 V0.8
T2000 N67 D500 V0.85

@mode human
play note(C5) @dur:w @vel:fff              // Final note in human
```

### Converting a .e File to .eci

Just rename it and add `@mode auto` at the top — the auto-detector handles mixed content:

```
@mode auto
// Now your file auto-detects machine vs human per line
T0 N60 D500 V0.8
T500 N64 D500 V0.7
play note(C4) @dur:q @vel:mf
C5 q ff
```

Use `.eci` when:
- You want the precision of machine for bass lines and readability of human for melodies
- You're collaborating with someone who prefers a different syntax
- You're gradually converting a machine file to human
- You're teaching someone and want to show both syntaxes side by side
- You need strict validation with `@mode strict`

---

## 33. .enx Root Index — The GOAT Format

> **`.enx` is the ultimate E format.** It's the master root index that ties everything together. You can compile, play, bundle, and distribute your entire project using nothing but a single `.enx` file. Think of it as the concert program for your album — or the entire album itself.

`.enx` is the master playlist. It lists `.ei` projects (or other `.enx` files) in order and plays them sequentially. Unlike `.ei` which is project-scoped, `.enx` is **album-scoped** — one file to rule them all.

### Why .enx Is the GOAT

| Task | Old Way | GOAT Way (`.enx`) |
|------|---------|-------------------|
| Compile an album | Compile each `.ei` separately | `compile album.enx -o album.mid` |
| Export to `.eic` | Bundle `.ei` then add `.enx` separately | `compile album.enx -o album.eic` — one step |
| Play a multi-movement work | Play each `.mid` file individually | `play album.enx` — plays everything in order |
| Share a complete album | Share `.ei` + `.enx` + parts/ folder | Share one `.eic` (bundled from `.enx`) |
| Distribute securely | Bundle `.ei` then encrypt | `compile album.enx -o album.ee` |

### Basic Album

### Basic Album

```
#ENX v1
project "My Piano Album"
composer "You"

order "movement1/mvmt1.ei"
order "movement2/mvmt2.ei" at 2000ms
order "movement3/mvmt3.ei" tempo 140
```

This plays `mvmt1.ei`, then waits 2 seconds of silence, then plays `mvmt2.ei`, then `mvmt3.ei` at 140 BPM (regardless of what BPM the .ei file has internally).

### Full Album Structure

Here's a complete album with multiple movements, each movement being its own `.ei` project:

```
#ENX v1
project "Nocturnes, Op. 1"
composer "Tentari"

// ── Part I: The Awakening ──
section "Part I — Evening" {
    order "movements/01_opening.ei"
    order "movements/02_reflection.ei" at 3000ms
    order "movements/03_shadows.ei" tempo 90
}

// ── Part II: The Dream ──
section "Part II — Night" {
    order "movements/04_nocturne.ei" at 2000ms
    order "movements/05_interlude.ei" tempo 55
    order "movements/06_climax.ei" at 1000ms tempo 180
}

// ── Part III: The Return ──
section "Part III — Dawn" {
    order "movements/07_resolution.ei" tempo 70
    order "movements/08_finale.ei" at 5000ms tempo 140
}
```

### .enx Linking to .ei — How They Connect

Every `order` points to an `.ei` project. The `.enx` doesn't care what's inside — it just plays them in sequence. Here's the relationship:

```
album.enx                     # The concert program
  │
  ├── order "01_intro.ei"    # Each .ei is a self-contained project
  │     └── index.ei          #   with its own include/play/section
  │           ├── parts/piano.e
  │           ├── parts/strings.e
  │           └── parts/bass.e
  │
  ├── order "02_verse.ei" at 2000ms
  │     └── index.ei
  │           └── parts/song.e
  │
  └── order "03_outro.ei" tempo 80
        └── index.ei
              ├── parts/fade.e
              └── parts/final_chord.e
```

### .enx Ordering Other .enx Files (Nested Albums)

An `.enx` can order other `.enx` files, creating nested album structures:

```
#ENX v1
project "Complete Symphony Cycle"
composer "Tentari"

// Each movement is itself an album of sections
section "Symphony No. 1" {
    order "symphony1/mvmts.enx"         // References another .enx!
}

section "Symphony No. 2" {
    order "symphony2/mvmts.enx" at 5000ms
}

section "Symphony No. 3" {
    order "symphony3/mvmts.enx" at 3000ms tempo 120
}
```

And `symphony1/mvmts.enx` might look like:

```
#ENX v1
project "Symphony No. 1 — Movements"
order "01_allegro.ei"
order "02_adagio.ei" at 3000ms tempo 55
order "03_minuet.ei" at 2000ms tempo 140
order "04_presto.ei" at 1000ms tempo 180
```

### .enx with Mixed .ei and Direct .e References

You can mix `.ei` projects and standalone `.e` files in the same `.enx`:

```
#ENX v1
project "Recital Program"

section "Opener" {
    order "intro/intro.ei"              // Full project
    order "cues/fanfare.e" tempo 160    // Single .e file as an order
}

section "Main Set" {
    order "sonata/sonata.ei"
    order "intermission.e" at 5000ms    // A simple .e interlude
    order "etudes/etude.ei" tempo 180
}
```

### .enx for Practice / Looping

Use `.enx` to create practice loops:

```
#ENX v1
project "Practice Session"
composer "Student"

order "exercise1.ei"
order "exercise1.ei" at 0ms           // Repeat immediately (builds endurance)
order "exercise2.ei" at 2000ms
order "exercise1.ei" at 5000ms        // Come back to it
order "exercise3.ei" at 2000ms
order "exercise1.ei" at 0ms           // Run it again
```

### .enx with Variable-Length Pauses

You can chain multiple `wait`-like pauses by using empty `.ei` projects or long `at` delays:

```
#ENX v1
project "Album with Intermissions"

order "act1.ei"
order "silence.ei" at 10000ms        // 10-second pause (silence.ei has no notes)
order "intermission_music.ei" tempo 80
order "silence.ei" at 8000ms
order "act2.ei"
```

A `silence.ei` file could be as simple as:

```
project "Silence"
tempo 120
section "Silence" {
    // nothing — intentionally empty
}
```

### Compile an Album

```powershell
E ...> compile album.enx -o complete_album.mid
```

### Compile and Play Directly

```powershell
E ...> play album.enx
```

The shell compiles the entire album and plays it in sequence.

### .enx Directives

| Directive | What It Does |
|-----------|-------------|
| `#ENX v1` | Format version marker (required) |
| `project "..."` | Album name |
| `composer "..."` | Your name |
| `order "path"` | Play an `.ei` or `.enx` or `.e` project |
| `order "path" at Nms` | Play after N ms of silence |
| `order "path" tempo N` | Override the project's BPM |
| `section "Name" { order ... }` | Group orders into named sections |
| `// comment` | Comments are ignored |

### Combining .enx + .ei Inheritance

The most powerful setup: use `.enx` to order projects, and each project uses `root` inheritance.

```
#ENX v1
project "Theme & 6 Variations"
composer "Mozart (AI)"

order "theme.ei"                    // The original theme
order "var1.ei" at 2000ms tempo 140  // Variation 1 (inherits from theme.ei)
order "var2.ei" at 2000ms tempo 90   // Variation 2
order "var3.ei" at 2000ms tempo 180  // etc.
order "var4.ei" at 2000ms tempo 70
order "var5.ei" at 2000ms tempo 200
order "var6.ei" at 3000ms tempo 140
```

Each `var1.ei` through `var6.ei` has `root "../theme.ei"` — so they all share the same base parts but override tempo, add new sections, or reorder the parts. See section 33.

---

## 34. .ei Inheritance — Reuse Projects as Building Blocks

You can make one `.ei` project inherit from another using the `root` directive. The child project gets all the parent's parts, variables, and settings.

### Parent: parent.ei

```
project "Base Theme"
tempo 100
include "parts/bass.e" as bass
include "parts/melody.e" as melody

section "Main" {
    play bass with melody
}
```

### Child: variation.ei

```
project "Variation"
root "parent.ei"
tempo 140

section "Fast Version" {
    play melody      // Inherited from parent!
    play bass after 500ms
}
```

### Multi-Level Inheritance (Grandparent → Parent → Child)

Inheritance chains can go as deep as you want:

```
grandparent.ei           ← Root theme, defines core instruments
    │
    ├── parent.ei        ← Inherits grandparent, adds a section
    │     │
    │     ├── child1.ei  ← Inherits parent, overrides tempo
    │     ├── child2.ei  ← Inherits parent, adds new part
    │     └── child3.ei  ← Inherits parent, recombines parts
```

**Grandparent:** `orchestra_base.ei`

```
project "Orchestral Base"
tempo 120
include "parts/strings.e" as strings
include "parts/winds.e" as winds
include "parts/brass.e" as brass
include "parts/percussion.e" as percussion

section "Tutti" {
    play strings with winds with brass with percussion
}
```

**Parent:** `movement_base.ei`

```
project "Movement Base"
root "../orchestra_base.ei"
tempo 100

// All 4 parts from grandparent are available
// Override the winds with a different arrangement
include "parts/winds_alt.e" as winds    // Replaces grandparent's winds

section "Strings Only" {
    play strings
}
section "Full Orchestra" {
    play strings with winds with brass with percussion
}
```

**Child:** `finale.ei`

```
project "Finale — Presto"
root "../movement_base.ei"
tempo 180

// Has: strings, winds (overridden), brass, percussion from grandparent
// Has: Strings Only, Full Orchestra sections from parent
// Adds its own:

include "parts/trumpet_solo.e" as solo

section "Intro" {
    play strings after 500ms
    play solo with winds
}
section "Finale Crescendo" {
    play Full Orchestra       // Calls parent's section!
    play solo after 2000ms
}
```

### Part Override Pattern

Override any inherited part by declaring `include` with the same name:

```
// Parent has: include "parts/bass.e" as bass
// Override in child:
include "parts/bass_heavy.e" as bass    // bass is now "bass_heavy.e"
```

The original part from the parent is replaced. All sections that refer to `bass` automatically use the new file.

### Section Override Pattern

You can't directly override a section, but you can create a new section with the same logic and simply not call the parent's sections:

```
project "Remix"
root "../original.ei"

// Parent has "Chorus" section — we ignore it
// We build our own:
section "My Chorus" {
    play melody with bass      // Same parts, new arrangement
    play drums after 1000ms    // Added drums
}
```

### Mix-In Pattern (Simulated Multiple Inheritance)

While E only supports single-inheritance chains, you can simulate mix-ins by having a base project that includes many parts and multiple children that cherry-pick:

```
// rhythm_section.ei — a "mixin" base
project "Rhythm Section"
include "parts/drums.e" as drums
include "parts/bass_guitar.e" as bass
include "parts/rhythm_guitar.e" as guitar
section "Groove" { play drums with bass with guitar }
```

```
// melody_project.ei — inherits rhythm + adds lead
project "Full Band"
root "rhythm_section.ei"
include "parts/lead_guitar.e" as lead
include "parts/vocals.e" as vox
section "Full Song" {
    play Groove                  // From rhythm_section
    play lead after 1000ms
    play vox after 2000ms
}
```

### Real-World Example: Symphony with Inheritance

```
Symphony/
├── orchestra_base.ei           ← Defines all instrument sections
├── movements/
│   ├── mvmt1_allegro.ei        ← Inherits orchestra_base
│   ├── mvmt2_adagio.ei         ← Inherits orchestra_base  
│   ├── mvmt3_minuet.ei         ← Inherits orchestra_base
│   └── mvmt4_presto.ei         ← Inherits orchestra_base
├── parts/
│   ├── violins.ei
│   ├── cellos.ei
│   ├── woodwinds.ei
│   ├── brass.ei
│   └── timpani.ei
└── full_symphony.enx           ← Orders all 4 movements
```

**full_symphony.enx:**
```
#ENX v1
project "Symphony in D Minor"
order "movements/mvmt1_allegro.ei"
order "movements/mvmt2_adagio.ei" at 3000ms
order "movements/mvmt3_minuet.ei" at 2000ms tempo 140
order "movements/mvmt4_presto.ei" at 2000ms tempo 180
```

Each movement `.ei` starts with `root "../orchestra_base.ei"` — they all share the same instrument parts but have different sections, tempos, and arrangements. The `.enx` plays them in concert order.

### Use Cases

- **Theme and variations**: Define a base theme, create variations that inherit it
- **Orchestration**: Define instrument parts in a base project, create movements that inherit and recombine
- **Collaboration**: Share a base project, let others create derivative works
- **Arrangement families**: Create "ballad version," "upbeat version," "jazz version" all inheriting the same melody

### Circular Reference Protection (DAG)

Both `.enx` albums and `.ei` inheritance can create circular dependencies — A references B which references A. E's compiler uses a **Directed Acyclic Graph (DAG) cycle detector** to catch these before they cause infinite recursion.

#### How It Works

A global `CompilationGraph` tracks every file currently being compiled. Before entering a new file (whether via `order` in `.enx` or `root` in `.ei`), the graph checks if that file is already in the current compilation stack:

```
album_A.enx         ← graph.enter(album_A)
  └── album_B.enx   ← graph.enter(album_B)
        └── album_A.enx  ← ← ← ALREADY IN STACK! CircularReferenceError!
```

#### What Triggers Detection

| Scenario | Detected? | Error Message |
|----------|-----------|---------------|
| `.ei` A roots to `.ei` B which roots to `.ei` A | ✓ Caught | `Circular reference: A → B → A` |
| `.enx` A orders `.enx` B which orders `.enx` A | ✓ Caught | `Circular reference: A → B → A` |
| `.enx` orders `.ei` which roots to a file in the same `.enx` chain | ✓ Caught (cross-format) | `Circular reference: A → B → C → B` |
| 3+ deep chains (A→B→C→A) | ✓ Caught | Shows the full chain |
| Deep but non-cyclic chains (A→B→C→D) | ✓ Passes through | No error |

#### What Happens When a Cycle Is Found

Instead of hitting Python's `RecursionError` (which crashes with an ugly stack trace), E prints a clear error and returns an empty event list:

```
✗ Circular reference detected: album_A.enx → album_B.enx → album_A.enx
```

The compilation continues (other files are unaffected), but the circular file and everything depending on it produce no output.

#### Best Practices to Avoid Cycles

1. **Keep inheritance trees shallow**: A → B → C is fine. A → B → C → A is not.
2. **Don't mix `.enx` and `.ei` roots in the same chain**: If `.enx` album A orders `.ei` project B, and B's `root` points to an `.ei` that's also ordered by A, you have a cross-format cycle.
3. **Use the `info` command to test**: `info file.ei` runs the compiler, which includes cycle detection. If it shows events, you're safe.
4. **One root base, many children**: The intended pattern is a single shared base with multiple children that inherit from it — not children that inherit from each other.

---

## 35. Import MIDI to E — Convert Any Song

Have a MIDI file from somewhere else? Convert it to E language.

### Single File

```powershell
E ...> convert song.mid -o song.e
```

This creates a `.e` file with human-readable syntax:

```
@bpm 120
play note(C4) @dur:q @vel:mf
play note(E4) @dur:e @vel:f
play note(G4) @dur:s @vel:pp
```

### From the CLI directly

```powershell
py -3 ep.py import song.mid -o song.e
```

### Import .ec Binary Files

```
py -3 ep.py import song.ec -o song.e
```

---

## 36. Import Audio to E — Transcribe from Sound

Convert WAV, MP3, MP4, MOV, FLAC, OGG, AAC — any audio file — into E language notes.

```powershell
E ...> convert piano_recording.wav -o transcribed.e
```

### How It Works

E uses FFT spectral analysis (Fast Fourier Transform) to detect pitches in the audio:

1. Load the audio file using FFmpeg
2. Split into short time frames (every ~12ms)
3. For each frame, find the strongest frequencies
4. Map frequencies to MIDI notes
5. Group into notes with onsets and durations

### Supported Audio Formats

`.wav`, `.mp3`, `.mp4`, `.m4a`, `.mov`, `.avi`, `.flac`, `.ogg`, `.aac`, `.wma`, `.aiff`

### Ghost Note Filter

When transcribing polyphonic audio, overlapping harmonics can create **ghost notes** — false detections caused by a loud note's upper harmonics (e.g., G4's 3rd harmonic masquerading as D6). E applies a post-transcription filter:

```
@transcribe:quality(standard)    # Default: harmonic subtraction + velocity filter
@transcribe:quality(draft)       # Fast, no ghost filtering
@transcribe:quality(high)        # Aggressive filtering, longer processing
```

The filter does three things:
1. **Harmonic subtraction** — after detecting a fundamental frequency, subtracts its harmonic series (2×, 3×, 4×, 5×) from the spectrum before looking for the next note
2. **Velocity threshold** — removes any note quieter than 15% of the loudest note in the track (likely harmonic residue)
3. **Onset deduplication** — if multiple notes start at the same timestamp, only the loudest is kept (others are likely harmonics); notes 3+ semitones apart are kept (they're real chord tones)

You can control the threshold from the command line:

```powershell
E ...> convert noisy_recording.wav -o clean.e --threshold 0.3 --min-dur 50
```

### Limitations

- Works best for **monophonic** audio (one note at a time)
- For polyphonic piano (multiple notes), results are approximate — the ghost filter helps but won't match ML-based transcription
- For best transcription quality, consider using dedicated ML tools (basic-pitch)
- Audio with heavy reverb, compression, or background noise will produce worse results

### From the CLI

```powershell
py -3 ep.py import piano_recording.wav -o song.e
```

---

## 37. MIDI → Full Human Project

To get a properly organized multi-file project from a MIDI file:

```powershell
E ...> convert song.mid --project
```

Or from CLI:

```powershell
py -3 ep.py import song.mid --project
```

This creates:

```
song_project/
├── index.ei              # Project index linking all parts
├── project.enx           # Root index (if multiple channels)
└── parts/
    ├── part_ch0.e        # Channel 0 — human-readable with note names
    ├── part_ch1.e        # Channel 1 — human-readable
    └── part_ch2.e        # Channel 2 — etc.
```

### What Makes It "Human"

Instead of machine tokens:

```
T0 N60 D500 V80
```

You get:

```
play note(C4) @dur:q @vel:mf
play note(D#4) @dur:e @vel:f
```

- MIDI numbers become note names (60 → C4)
- Durations become codes (500ms at 120 BPM → `q`)
- Velocity numbers become Italian terms (80 → `mf`)
- Each MIDI channel gets its own file
- An `.ei` index ties everything together
- A `.enx` root is generated for multi-channel projects

---

## 38. .ec Compiled Binary — Fast Load

For very large files, `.ec` is a pre-compiled binary format that loads instantly — no parsing needed.

### Export

```powershell
E ...> compile huge_song.e -o huge_song.ec
```

### Import Back

```powershell
E ...> convert huge_song.ec -o huge_song.e
```

### Binary Format

```
EC\x01\x00            # Magic number (4 bytes)
BPM                   # 4-byte float
Event count           # 4-byte unsigned int
Total duration        # 4-byte unsigned int
Reserved              # 8 bytes padding
Event 1               # 12 bytes (timestamp, MIDI, duration, velocity, pan, bend)
Event 2
...
```

---

## 39. .eic Clear Bundle — One File to Share

`.eic` combines a project's index and all its parts into a single human-readable file. Perfect for sharing.

**Supports all formats:** `.e`, `.ei`, and **`.enx`** (albums). Any project type can be bundled into a single `.eic` file.

### Generate from `.e`

```powershell
E ...> compile song.e -o song.eic
```

### Generate from `.ei` Project

```powershell
E ...> compile project/index.ei -o project.eic
```

### Generate from `.enx` Album (THE GOAT)

The `.enx` file is now the **primary first-class format** for `.eic` bundling. An `.enx` album — with all its ordered `.ei`/`.e` projects — can be bundled into one `.eic` that contains everything:

```powershell
E ...> compile album.enx -o complete_album.eic
```

This bundles:
- The `.enx` album header (project name, composer, all `order` directives)
- Every `.ei` project referenced in the `order` lines
- Every `.e` part file inside each `.ei` project
- All source code inline — one file, zero dependencies

### What's Inside (`.ei` → `.eic`)

```
// EIC — E Index Clear
// Generated from: my_project.ei

// ===== PROJECT INDEX =====
project "Symphony"
tempo 120
include "parts/theme.e" as theme
...

// ===== parts/theme.e =====
@bpm 120
T0 N60 D500 V0.8
...

// ===== parts/bass.e =====
@bpm 120
T0 N36 D500 V0.7
...
```

### What's Inside (`.enx` → `.eic`)

```
// EIC — E Index Clear
// Generated from: album.enx

// ===== ALBUM ROOT (.enx) =====
project "My Symphony Album"
composer "You"

order "movements/mvmt1.ei"
order "movements/mvmt2.ei" at 2000ms tempo 140

// ===== ORDERED PROJECTS =====

// --- Order 1: movements/mvmt1.ei ---
// order "movements/mvmt1.ei"
// Project: Movement 1
//   Part: melody

// ===== movements/mvmt1.ei :: melody =====
@bpm 120
T0 N60 D500 V0.8
...

// --- Order 2: movements/mvmt2.ei at 2000ms tempo 140 ---
// order "movements/mvmt2.ei" at 2000ms tempo 140
// Project: Movement 2
//   Part: bass

// ===== movements/mvmt2.ei :: bass =====
@bpm 140
T0 N36 D1000 V0.7
...
```

Everything is plain text. You can edit it with any text editor, and it compiles natively. The `.eic` preserves the original `.enx` structure including delays (`at Nms`) and tempo overrides.

### Compile a `.eic` Back to Audio

Since `.eic` is native E format, you compile it just like any other file:

```powershell
E ...> compile album.eic -o album.mid
E ...> compile album.eic -o album.wav
E ...> compile album.eic -o album.mp3
```

---

## 40. Export to .wav / .mp3 / .mp4

E can render your music to audio files using the built-in MIDI synthesizer and FFmpeg.

```powershell
E ...> compile song.e -o song.wav       # Uncompressed audio
E ...> compile song.e -o song.mp3       # Compressed audio (320kbps)
E ...> compile song.e -o song.mp4       # Video with piano roll animation
```

### Audio Quality Settings

```
@sr:44100             # CD quality (default)
@sr:48000             # Professional audio
@sr:96000             # High-resolution

@bit:16               # 16-bit (CD standard, default)
@bit:24               # 24-bit (studio quality)
@bit:32               # 32-bit float (highest)

@quality:draft        # Fast, lower quality
@quality:standard     # Balanced (default)
@quality:mastering    # Maximum quality
```

---

## 41. Signing & Encryption — Protect Your Work

### Sign Your Files

Add your name and social links so people know it's yours.

```powershell
E ...> sign song.eic
Author> Tentari
Instagram> @tentari
Discord> pixelhollow
✓ Signed
```

Signatures use HMAC-SHA256 and can be:
- **Embedded** (inside `.eic`, `.ec`, `.ee`, `.ecc` files)
- **Sidecar** (separate `.sig` file for `.mid`, `.wav`, `.mp3`)

### Verify a Signature

```powershell
E ...> info song.eic
```

### Encrypt Your Files

Protect your music with AES-256-GCM encryption.

```powershell
E ...> encrypt song.e -o song.ee       # Encrypt a .e file
E ...> encrypt my_project.ei -o project.ee  # Bundle + encrypt entire project
```

To decrypt and compile:

```powershell
E ...> compile song.ee -o song.mid     # Decrypt then compile to MIDI
```

### Encrypt + Sign in One Step

```powershell
E ...> compile song.e -o song.ee --sign
```

---

## 42. Garbage Collection — Clean Up Messy Generations

When you generate music (especially with AI or randomization), you can get overlapping notes, duplicates, or out-of-range errors. GC cleans that up.

### Built-in Strategies

```
@gc:auto          # Default — remove duplicates, bad notes, zero durations
@gc:aggressive    # Also merges overlapping same-pitch notes
@gc:off           # Skip GC (debugging only)
```

### What Each Strategy Does

| Cleanup Step | auto | aggressive |
|-------------|------|------------|
| Remove notes outside MIDI 0–127 | ✓ | ✓ |
| Remove zero-duration events | ✓ | ✓ |
| Remove duplicate events | ✓ | ✓ |
| Clamp velocity to 0–127 | ✓ | ✓ |
| Merge overlapping same-pitch notes | — | ✓ |

---

## 43. Low-Level Sound Control — For Perfectionists

### Micro-Timing (Swing)

Shift notes by tiny amounts:

```
@micro:0.1ms              # 100 microsecond precision
@micro:swing(30ms)        # Micro-delay swing feel
@phase:90                 # Phase offset in degrees
```

### Micro-Pitch (Cents)

Tune notes micro-scopically:

```
@cents:+12                # 12 cents sharp (≈ ⅛ semitone)
@cents:-50                # 50 cents flat (quarter-tone down)
```

Or per-note with `P[bend:]`:

```
T0 N60 D500 V0.8 P[bend:-50]    # 50 cents flat
```

### Envelope Shaping

Control how each note's volume changes over time:

```
@attack:0.5ms             # How fast the note reaches full volume (sharp)
@attack:50ms              # Slower attack (soft, like strings)
@decay:100ms              # How fast it drops to sustain level
@sustain:0.7              # The volume while holding the note
@release:200ms            # How long it takes to fade after release
```

### Filter Control

Shape the tone:

```
@filter:lowpass(cutoff=2000hz, resonance=0.5)   # Muffled, warm
@filter:highpass(cutoff=80hz)                     # Remove bass rumble
@filter:bandpass(center=440hz, q=2.0)             # Telephone effect
```

### Stereo Imaging

```
@stereo:width(100%)        # Normal stereo
@stereo:width(50%)         # Narrower
@stereo:width(200%)        # Wider (enhanced)
```

### Extended #MACHINE Tokens

```
T0 N60 D500 V0.8 F[c:2000hz] F[r:0.5] F[t:lowpass] E[a:1ms] E[r:300ms] Z[ph:90]
```

| Token | Example | What It Controls |
|-------|---------|-----------------|
| `F[c:]` | `F[c:2000]` | Filter cutoff frequency (Hz) |
| `F[r:]` | `F[r:0.5]` | Filter resonance (0.0–1.0) |
| `F[t:]` | `F[t:lowpass]` | Filter type (lowpass/highpass/bandpass) |
| `E[a:]` | `E[a:0.5ms]` | Envelope attack time |
| `E[r:]` | `E[r:200ms]` | Envelope release time |
| `E[s:]` | `E[s:0.7]` | Envelope sustain level |
| `Z[ph:]` | `Z[ph:90]` | Phase offset (degrees) |
| `Z[pt:]` | `Z[pt:+12]` | Micro-pitch (cents) |
| `Z[sw:]` | `Z[sw:30ms]` | Swing timing offset |

### Extended #HUMAN Properties

```
play note(C2) @dur:w @sub:40hz @filter:lowpass(80hz,0.8) @attack:2ms @release:500ms
play note(C4) @dur:q @vel:mf @micro:0.5ms @cents:-5 @pan:-0.3
```

---

## 44. Audio Driver System — Pick Your Output

E can detect and use different audio devices (speakers, headphones, virtual cables).

### List Devices

```
E ...> audio devices
```

Shows all available audio outputs with driver type (WASAPI, DirectSound, MME, WDM-KS).

### Set Device

```
E ...> audio set-device 2      # Use device #2
E ...> audio config            # Show current audio config
```

### Audio Config Persistence

Settings are saved to `audio_config.json` and persist across sessions.

---

## 45. HELLFORGE Ecosystem & CORE-EXPANSION: REGAS

**HELLFORGE** is the v0.1.0-beta release of the E language ecosystem, combining the E compiler with GPU shader math, Tensor Core acceleration, OpenGL/Vulkan graphics APIs, and 3D spatial audio.

### Trust System

| Level | Name | Meaning |
|-------|------|---------|
| 2 | **REGAS** | CORE-EXPANSION — server-confirmed TENTARI, utmost trust |
| 2 | **TENTARI** | Third-party plugin devs, same trust level |
| 1 | **UNKNOWN** | Unknown signer, key not in trusted store |
| 0 | **UNSIGNED** | No signature or invalid |

- **REGAS** plugins are TENTARI-verified through the oshonet.in backend — no doubt about authenticity
- **TENTARI** plugins can be signed by any third-party developer with their own ed25519 keypair
- Signing is mandatory for plugin distribution; enforcement level via `sys strict <0|1|2>`
- See [doc/signing/overview.md](doc/signing/overview.md) for full documentation

### Evaluator Priority Chain

```
Priority 3: TensorSHARP → NVIDIA Tensor Cores (CuPy + CUDA)
Priority 5: Radical → GPU shader cores (GLSL compute shaders)
Priority 10: LURE → LuaJIT CPU acceleration
Priority 100: Python → Pure Python fallback (always works)
```

### Plugin Load Order (boot)

1. Radical (GPU detect → compute runtime)
2. TensorSHARP (CuPy → Tensor Cores)
3. OPENapi (OpenGL context → rendering API)
4. Vulkanizer (Vulkan instance → compute/Ray Tracing API)
5. EAudio (Audio device → 3D spatial audio API)
6. LURE (LuaJIT → batch parsing accelerator)
7. Fentclient (Bug fixes → security → async engine)
8. Portbaby (Syntax version conversion)
9. Talisman (Audio culling → privacy)

### Dependency Chain

- **OPENapi** requires **Radical** for GPU context
- **Vulkanizer** requires **Radical** for GPU detection
- **TensorSHARP** requires **Radical** for fallback compute
- **EAudio** requires **Radical** for GPU audio DSP

Third-party plugins declare dependencies via `api.require("PluginName")`.

See [doc/index.md](doc/index.md) for the full HELLFORGE wiki (60+ pages).

---

## 46. GPU Shader Math (Radical Plugin)

Radical compiles E math expressions (`{$bpm * 2}`, `sin($i * 0.5)`) into GLSL compute shaders and executes them on GPU shader cores.

- Registered as math evaluator at **priority 5** (above LURE's 10)
- Auto-detects all GPUs: NVIDIA, AMD, Intel Arc/UHD/Iris, Apple M-series, Qualcomm
- Supports multi-GPU switching: `radical gpu <index>`
- VRAM limit: `radical vram <MB>`
- GLSL codegen from E AST for all math functions (sin, cos, sqrt, pow, quadratic, etc.)
- Batch evaluation: 256+ expressions in a single GPU dispatch
- Matrix operations: matmul, transpose, conv2d (GPU → numpy → CPU fallback)

### Commands

```
radical status     — Show GPU info, all detected GPUs, API support
radical gpu <idx>  — Switch active GPU (multi-GPU systems)
radical vram <MB>  — Set max VRAM limit
radical benchmark  — Compare GPU vs CPU speed
radical shaders    — Show compiled shader cache
radical info       — Plugin info
```

See [doc/plugins/radical.md](doc/plugins/radical.md) for full documentation.

---

## 47. Tensor Core Acceleration (TensorSHARP Plugin)

TensorSHARP accelerates matrix-heavy math using NVIDIA Tensor Cores via CuPy (CUDA).

- Registered as math evaluator at **priority 3** (highest)
- Requires CuPy + CUDA toolkit + NVIDIA GPU with Tensor Cores (SM 7.0+)
- Uses TF32 mixed precision on Ampere (RTX 30xx/40xx), FP16 on Volta/Turing
- Auto-detects CUDA toolkit by probing common install paths and env vars
- Matmul benchmark vs Radical (shader cores) vs CPU

### Commands

```
tensorsharp status     — CUDA version, Tensor Core count, precision
tensorsharp cores      — Detailed Tensor Core config (TF32/FP16/INT8)
tensorsharp benchmark  — Matmul speed comparison
tensorsharp info       — Plugin info
```

See [doc/plugins/tensorsharp.md](doc/plugins/tensorsharp.md) for full documentation.

---

## 48. OpenGL Graphics API (OPENapi Plugin)

OPENapi provides low-level OpenGL primitives for building game engines, visualizers, and GPU-accelerated UIs. It is **not a game engine** — game engines are built **on top** of it.

### API Modules

| Module | Description |
|--------|-------------|
| `_context.py` | GLFW window, OpenGL version, extensions, debug callback |
| `_shader.py` | GLSL compile/link, uniform reflection |
| `_buffer.py` | VBO, VAO, EBO, SSBO, UBO allocation + upload |
| `_texture.py` | 2D/3D/cubemap textures, sampler state, mipmaps |
| `_render.py` | Pipeline state, draw calls, framebuffer objects |
| `_window.py` | Input callbacks, cursor modes, fullscreen toggling |

### Usage Pattern

```python
from plugins.openapi._context import GLContext
from plugins.openapi._api import OpenGLAPI

ctx = GLContext(width=1920, height=1080, title="My Game")
api = OpenGLAPI(ctx)
api.shader.compile(vertex_src, fragment_src, "my_shader")
api.buffer.create_vbo(vertices)
api.render.draw_arrays(...)
```

See [doc/plugins/openapi.md](doc/plugins/openapi.md) and [examples/opengl_engine.py](examples/opengl_engine.py).

---

## 49. Vulkan Compute + Ray Tracing (Vulkanizer Plugin)

Vulkanizer provides low-level Vulkan primitives for compute shaders, hardware ray tracing, and custom temporal upscaling. Game engines are built **on top** of it.

### API Modules

| Module | Description |
|--------|-------------|
| `_instance.py` | Vulkan instance, physical device selection, queues |
| `_pipeline.py` | Compute/graphics pipelines, shader modules, descriptor sets |
| `_buffer.py` | Device-local/host-visible buffers, staging, barriers |
| `_command.py` | Command pools, command buffers, submit, sync (fences/semaphores) |
| `_raytrace.py` | VK_KHR_ray_tracing — BLAS/TLAS, SBT, ray dispatch |
| `_upscale.py` | Custom temporal upscaling via compute shaders + Tensor Cores |

### Ray Tracing

- Requires `VK_KHR_acceleration_structure`, `VK_KHR_ray_tracing_pipeline`
- Hardware RT on NVIDIA RTX (Turing+), AMD RX 6000+, Intel Arc A3+
- Build BLAS from geometry, TLAS from instances, dispatch with SBT

### Custom Upscaling

- Temporal upscaling (like DLSS but fully custom pipelines)
- Uses Tensor Cores when available via CuPy matmul
- Falls back to compute shaders (any GPU)
- Anti-ghosting via temporal feedback (previous frame lerp)

See [doc/plugins/vulkanizer.md](doc/plugins/vulkanizer.md).

---

## 50. 3D Spatial Audio (EAudio Plugin)

EAudio provides low-level audio primitives for device management, PCM buffers, 3D spatial positioning, and DSP effects. Audio engines are built **on top** of it.

### API Modules

| Module | Description |
|--------|-------------|
| `_device.py` | Audio device enumeration, selection, format negotiation |
| `_buffer.py` | PCM buffer creation, mixing, resampling, sine/silence generation |
| `_spatial.py` | 3D positioning, listener/source velocity, doppler shift, distance attenuation |
| `_effects.py` | Reverb, delay, compressor, 3-band EQ |

### Spatial Audio

```python
spa.set_listener([0, 0, 0], velocity=[0, 0, 0])
spa.add_source("engine", [10, 0, 0], velocity=[5, 0, 0])
spa.update_source("engine", [12, 3, -1])
left_gain, right_gain = spa.get_spatial_gain("engine")
shifted_rate = spa.doppler_shift("engine", 44100)
```

### DSP Effects

```python
effects.reverb(buffer, decay=0.5, delay_ms=30)
effects.delay(buffer, delay_ms=200, feedback=0.4)
effects.compressor(buffer, threshold=0.5, ratio=4.0)
effects.eq(buffer, bass_gain=1.2, mid_gain=1.0, treble_gain=1.1)
```

See [doc/plugins/eaudio.md](doc/plugins/eaudio.md).

---

## 51. LuaJIT Accelerator (LURE Plugin)

LURE accelerates compilation using LuaJIT (via `lupa`). It provides batch line parsing, scale quantization, and math expression evaluation at 3-10x speedup over Python.

- Registered as math evaluator at **priority 10**
- GIL-free execution — lupa releases the GIL during LuaJIT runs
- Async engine with per-thread LuaRuntimes for parallel compilation
- Batch parsing: 1000+ lines in a single LuaJIT dispatch
- Scale quantization, MIDI tick calculation, event validation all in Lua
- Graceful fallback to Python if `lupa` is not installed

### Commands

```
lure status      — Sync/async engine status, parse stats
lure benchmark   — Compare Python vs LURE speeds
lure async       — Benchmark async batch compile
```

See [doc/plugins/lure.md](doc/plugins/lure.md).

---

## 52. Plugin & Mod System — Extend E

E's plugin and mod system lets anyone extend the language with custom commands, syntax, variables, encryption, GC strategies, and eshell integrations. There are two types of extensions:

| Type | Directory | Entry Point | Safety Scan | Use Case |
|------|-----------|-------------|-------------|----------|
| **Plugin** | `plugins/` | `register(api)` | None (trusted) | Full API access, eshell commands, all hooks |
| **Mod** | `mods/` | `init(api)` | Security-scanned | Lightweight extensions, sandboxed |

Both receive the same `api` object with all methods.

---

### How Plugins Work

When eshell or ep.py starts, it scans the `plugins/` directory for `.py` files. Each file's `register(api)` function is called with the Plugin API object. The plugin can then:

- Add new eshell commands
- Register custom syntax parsers
- Register custom `$variable` handlers
- Add encryption methods
- Hook into compilation/playback events
- Modify the shell theme and prompt
- Add output filters
- Register custom GC strategies

#### Directory

```
piano-dsl/plugins/
├── my_plugin.py        ← Your plugin
├── another_plugin.py   ← Another plugin
└── _disabled/          ← Files starting with _ are ignored
```

#### Minimal Plugin

```python
# plugins/hello_world.py
def register(api):
    api.add_command("hello", lambda args: print("  Hello from E plugin!"), "Say hello")
```

Drop this file in `plugins/`, restart eshell, and:

```
E ...> hello
  Hello from E plugin!
```

---

### Plugin API v2 — Full Reference

The `api` object passed to `register()` has all these methods:

#### `api.add_command(name, handler, help_text="")`
Add a new eshell command. `handler` receives a list of string arguments.

```python
def register(api):
    def greet(args):
        name = " ".join(args) if args else "world"
        print(f"  Hello, {name}!")

    api.add_command("greet", greet, "Greet someone: greet <name>")
```

Now in eshell:
```
E ...> greet Tentari
  Hello, Tentari!
E ...> greet
  Hello, world!
```

#### `api.register_syntax(handler)`
Register a custom syntax parser. Handler receives a line of text and a state dict. If it recognizes the line, it returns an event dict (or list of events). If not, returns None.

```python
def register(api):
    import re
    DICE_RE = re.compile(r'^roll\s+(\d+)d(\d+)$', re.I)

    def parse_dice(line, state):
        m = DICE_RE.match(line)
        if not m:
            return None  # Not our syntax — let other parsers try
        import random
        count, sides = int(m.group(1)), int(m.group(2))
        total = sum(random.randint(1, sides) for _ in range(count))
        print(f"  Rolled {count}d{sides}: {total}")
        # Return empty event list (it's a directive, not a note)
        return {"timestamp": 0, "midi": 60, "duration": 1, "velocity": 0, "silent": True}

    api.register_syntax(parse_dice)
```

#### `api.register_variable_handler(handler)`
Handle custom `$variable` expansion. Handler gets the variable name and current state, returns replacement text or None.

```python
def register(api):
    import datetime

    def handle_var(name, state):
        if name == "time":
            return datetime.datetime.now().strftime("%H:%M")
        if name == "date":
            return datetime.datetime.now().strftime("%Y-%m-%d")
        return None  # Not our variable

    api.register_variable_handler(handle_var)
```

Now `$time` and `$date` expand in any `.e` file:
```
// This comment shows the current time: $time
// Today's date: $date
T0 N60 D500 V0.8
```

#### `api.register_encryptor(name, encrypt_fn, decrypt_fn)`
Add a custom encryption method for `.ee` files. Both functions take `(data: bytes, key: str) -> bytes`.

```python
def register(api):
    def my_encrypt(data, key):
        # Rot13-like cipher for demonstration (NOT secure)
        import codecs
        return codecs.encode(data.decode(), "rot_13").encode()

    def my_decrypt(data, key):
        import codecs
        return codecs.encode(data.decode(), "rot_13").encode()

    api.register_encryptor("rot13", my_encrypt, my_decrypt)
```

Now:
```
E ...> encrypt song.e -o song.ee   # Uses "base" encryptor by default
```

#### `api.add_command(name, handler, help_text)`
Add a command to eshell (see detailed example above).

#### `api.add_keybinding(key, action, description="")`
Add a keyboard shortcut for eshell. Key format: `ctrl+p`, `alt+x`, etc.

```python
def register(api):
    def clear_and_list(args):
        import os
        os.system("cls" if os.name == "nt" else "clear")
        print("  Cleared!")

    api.add_keybinding("ctrl+l", clear_and_list, "Clear and show banner")
```

#### `api.set_prompt_renderer(renderer)`
Customize the eshell prompt. Renderer receives the current working directory string, returns a prompt string.

```python
def register(api):
    def my_prompt(cwd):
        short = cwd.split("\\")[-1] if "\\" in cwd else cwd.split("/")[-1]
        return f"\033[95m♪\033[0m \033[90m{short}\033[0m \033[92m>\033[0m "

    api.set_prompt_renderer(my_prompt)
```

Now the prompt looks like:
```
♪ project >
```

Multiple renderers can be registered — they all run and the last one wins.

#### `api.add_output_filter(filter_fn)`
Transform ALL eshell output before it's displayed. Function gets text, returns modified text.

```python
def register(api):
    def uppercase(text):
        return text.upper()

    api.add_output_filter(uppercase)
```

Now everything in eshell is UPPERCASE. Multiple filters can be chained.

#### `api.on(event, callback)`
Hook into E lifecycle events. Callback receives no arguments (for now).

```python
def register(api):
    def before_compile():
        print("  Compilation starting...")

    def after_compile():
        print("  Compilation complete!")

    api.on("pre_compile", before_compile)
    api.on("post_compile", after_compile)
```

#### `api.register_gc(name, strategy_fn)`
Register a custom garbage collection strategy. Strategy function receives a list of events, returns cleaned list.

```python
def register(api):
    def remove_piano_notes(events):
        """Remove all notes in the piano range (MIDI 48-72)."""
        return [e for e in events if not (48 <= e.get("midi", 0) <= 72)]

    api.register_gc("no_piano", remove_piano_notes)
```

Use it in any `.e` file:
```
@gc:no_piano
T0 N60 D500 V0.8    # This gets removed!
T0 N36 D500 V0.7    # This stays (bass note)
```

#### `api.set_theme(**kwargs)`
Override eshell theme colors and appearance.

```python
def register(api):
    api.set_theme(
        prompt_color="\033[95m",     # Magenta prompt
        accent_color="\033[93m",     # Yellow accents
        dim_color="\033[90m",        # Grey dim text
        error_color="\033[91m",      # Red errors
        success_color="\033[92m",    # Green success
        warning_color="\033[93m",    # Yellow warnings
        banner_art="",               # Custom banner text (empty = default)
        prompt_char="★",             # Prompt character
    )
```

#### `api.log(msg)`
Print a message to the console. Same as `print()` but goes through the plugin system.

```python
def register(api):
    api.log("Hello from my plugin!")
```

#### `api.project_dir`
Property returning the absolute path to the E project directory.

```python
def register(api):
    print(f"  Project dir: {api.project_dir}")
```

#### `api.commands`
Property returning a dict of all registered eshell commands.

```python
def register(api):
    for name, (handler, help_text) in api.commands.items():
        print(f"  Command: {name} — {help_text}")
```

#### `api.theme`
Property returning the current theme dict.

```python
def register(api):
    print(f"  Current prompt char: {api.theme['prompt_char']}")
```

---

### Event Hooks — Full Reference

| Event | When It Fires | Use Case |
|-------|--------------|----------|
| `pre_compile` | Before compilation starts | Logging, validation, resource setup |
| `post_compile` | After compilation finishes | Stats, cleanup, auto-export |
| `pre_play` | Before playback starts | Volume normalization, device switching |
| `post_play` | After playback finishes | Logging, cleanup |
| `pre_render` | Before audio rendering | Filter setup, quality override |
| `post_render` | After audio rendering | File renaming, notification |
| `on_load` | When plugin is loaded | Initialization, config loading |
| `on_unload` | When plugin is unloaded | Cleanup, saving state |
| `on_exit` | When the shell exits | Saving config, sending telemetry |

---

### Complete Plugin Example

Here's a full-featured plugin that adds a `count` command, hooks into compile events, and customizes the prompt:

```python
# plugins/stats_plugin.py
"""
E Stats Plugin — Adds counting and statistics to eshell.
"""

def register(api):
    # ── Command: count notes in a file ──
    def count_notes(args):
        if not args:
            print("  Usage: count <file.e>")
            return
        path = " ".join(args).strip("\"'")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            from ep_compiler.compile import compile_source
            events, bpm = compile_source(text)
            total_dur = max((e["timestamp"] + e["duration"] for e in events), default=0)
            print(f"  Notes: {len(events)}")
            print(f"  Duration: {total_dur/1000:.1f}s")
            print(f"  BPM: {bpm}")
        except Exception as e:
            print(f"  Error: {e}")

    api.add_command("count", count_notes, "Count notes in a .e file")

    # ── Hook into compile events ──
    def on_pre_compile():
        print("  [Stats] Compilation starting...")

    def on_post_compile():
        print("  [Stats] Compilation done!")

    api.on("pre_compile", on_pre_compile)
    api.on("post_compile", on_post_compile)

    # ── Custom prompt ──
    def custom_prompt(cwd):
        short = cwd.split("\\")[-1].split("/")[-1]
        return f"\033[96mE>\033[0m "

    api.set_prompt_renderer(custom_prompt)

    # ── Log that we loaded ──
    api.log("  Stats plugin loaded!")
```

---

### How Mods Work

Mods are like plugins but **security-scanned**. Before a mod is loaded, E checks its source code for dangerous patterns:

```python
SECURITY_BLOCKLIST = [
    "os.system", "os.popen",
    "subprocess.Popen", "subprocess.call", "subprocess.run",
    "shutil.rmtree",
    "__import__('os')",
    "eval(", "exec(", "compile(",
    "pty.spawn", "ctypes.CDLL", "win32api",
    "socket.connect", "requests.get",
]
```

If any of these patterns are found, the mod is **rejected** and not loaded.

#### Mod Entry Point

```python
# mods/my_mod.py
def init(api):
    api.log("My mod loaded!")

    def mod_command(args):
        print(f"  Mod says: {' '.join(args) if args else 'hi'}")

    api.add_command("mod_cmd", mod_command, "A command from a mod")
```

#### Difference Between Plugins and Mods

| Aspect | Plugin | Mod |
|--------|--------|-----|
| Safety scan | None | Blocked for dangerous patterns |
| Entry point | `register(api)` | `init(api)` |
| Use case | Full-featured extensions | Lightweight, distributable |
| Distribution | EZip or direct drop-in | EZip with security scan |
| Can add commands | Yes | Yes |
| Can add syntax | Yes | Yes (but limited) |

---

### Making an EZip Package

EZip is the distribution format for plugins and mods. It's a ZIP file with a specific structure.

#### EZip Structure

```
my_extension.ezip
├── EzPk                      # Required — magic marker file (empty or with data)
├── manifest.json             # Required — package metadata
├── main.py                   # Required — entry point
├── assets/                   # Optional — additional files
│   ├── config.json
│   └── template.e
└── requirements.txt          # Optional — Python dependencies
```

#### manifest.json — Full Spec

```json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "type": "plugin",
    "entry": "main.py",
    "author": "Tentari",
    "description": "Adds waltz patterns to E language",
    "tags": ["rhythm", "patterns", "waltz"],
    "min_engine_version": "2.0.0",
    "max_engine_version": "3.0.0",
    "dependencies": ["numpy>=1.20"],
    "license": "MIT",
    "homepage": "https://github.com/tentari/e-waltz",
    "update_url": "https://example.com/updates/waltz.py",
    "eshell_help": "waltz <bpm> — Generate waltz accompaniment"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Package name (used for installation path) |
| `version` | Yes | Semantic version string |
| `type` | Yes | `"plugin"` or `"mod"` |
| `entry` | Yes | Entry point filename (usually `main.py`) |
| `author` | No | Creator name |
| `description` | No | Short description (shown in `pkglist search`) |
| `tags` | No | Array of tag strings for search |
| `min_engine_version` | No | Minimum E engine version required |
| `max_engine_version` | No | Maximum E engine version supported |
| `dependencies` | No | Python package dependencies (pip-installable) |
| `license` | No | SPDX license identifier |
| `homepage` | No | Project website |
| `update_url` | No | Direct URL for auto-updates |
| `eshell_help` | No | Help text shown in eshell `help` |

#### Creating an EZip Package by Hand

```powershell
# 1. Create the directory structure
mkdir my_package
cd my_package

# 2. Create manifest.json
echo '{"name":"my_package","version":"1.0.0","type":"mod","entry":"main.py","author":"You"}' > manifest.json

# 3. Create the entry point (main.py)
echo 'def init(api):' > main.py
echo '    api.add_command("mypkg", lambda a: print("hello"), "My command")' >> main.py

# 4. Create the EzPk magic marker
echo -n "EzPk" > EzPk

# 5. Zip it up
..\tools\zip -r ../my_package.ezip .
```

Or using Python:

```python
import zipfile, json
with zipfile.ZipFile("my_package.ezip", "w") as zf:
    zf.writestr("EzPk", "EzPk")
    zf.writestr("manifest.json", json.dumps({
        "name": "my_package", "version": "1.0.0",
        "type": "mod", "entry": "main.py", "author": "You"
    }))
    zf.writestr("main.py", "def init(api):\n    api.add_command('mypkg', lambda a: print('ok'), 'test')\n")
```

#### Installing an EZip

```powershell
E ...> ezip install my_package.ezip          # Installs as mod
E ...> ezip install my_package.ezip --plugin # Installs as plugin
E ...> ezip list my_package.ezip             # Preview contents
E ...> ezip info my_package.ezip             # Show metadata
```

---

### Package Manager — pkglist System

E has a built-in package registry system for discovering and downloading mods and plugins.

#### Package List File

The package list is stored in `pkglist.json` in the project root:

```json
{
    "version": "2.0.0",
    "updated": "2024-12-25T12:00:00",
    "url": "http://localhost:5592/api",
    "mods": {
        "cool_mod": {
            "version": "1.2.0",
            "description": "Adds swing rhythm patterns",
            "author": "Tentari",
            "tags": "rhythm,swing",
            "url": "http://example.com/mods/cool_mod.py"
        }
    },
    "plugins": {
        "viz_plugin": {
            "version": "2.0.1",
            "description": "Real-time piano roll visualization",
            "author": "Community",
            "tags": "visualization,ui",
            "url": "http://example.com/plugins/viz.py"
        }
    }
}
```

#### pkglist Commands

##### `pkglist show`
Display current registry URL and package counts:

```
E ...> pkglist show
  Registry: http://localhost:5592/api
  Mods: 12
  Plugins: 8
  Last updated: 2024-12-25T12:00:00
```

##### `pkglist update url <URL>`
Set a new registry URL and synchronize the package list:

```
E ...> pkglist update url https://e-packages.example.com/api
  ⟳ fetching pkglist  https://e-packages.example.com/api
  ✓ synced  24 mods, 15 plugins
```

The URL should point to a JSON endpoint that returns a package list in the format above.

##### `pkglist update file <path>`
Load a package list from a local JSON file:

```
E ...> pkglist update file ./my_packages.json
  ✓ loaded  5 mods, 3 plugins
```

##### `pkglist search <query>`
Search the registry for packages matching a keyword:

```
E ...> pkglist search waltz
  🔍 Search results (3 matches)
    [mod] waltz_generator v1.0.0  Generates waltz bass patterns
    [plugin] waltz_viz v2.1.0    Visualizes waltz rhythm
    [mod] threefour v0.5.0       Waltz time utilities
```

Search checks the package name, description, and tags for matches.

##### `pkglist version`
Show the package manager version:

```
E ...> pkglist version
  pkglist v2.0.0
```

##### `pkglist detail <name>`
Show detailed information about a specific package:

```
E ...> pkglist detail waltz_generator
  Package: waltz_generator
  Version: 1.0.0
  Type: mod
  Author: Tentari
  Description: Generates waltz bass patterns (oom-pah-pah)
  Tags: rhythm, waltz, accompaniment
  URL: http://example.com/mods/waltz_generator.py
```

---

### mod Commands — Full Reference

| Subcommand | Description | Example |
|------------|-------------|---------|
| `list` | Show installed mods | `mod list` |
| `scan` | Security-scan all mods | `mod scan` |
| `available` | List mods available in registry | `mod avail` |
| `fetch <name>` | Download and install from registry | `mod fetch cool_mod` |
| `update <name>` | Update a specific mod | `mod update cool_mod` |
| `update --all` | Update all mods with update_url | `mod update --all` |
| `remove <name>` | Uninstall a mod | `mod remove old_mod` |
| `version` | Show mod system version | `mod version` |

#### `mod list`
Shows installed mods with version and author:

```
E ...> mod list
  📦 Installed Mods
  my_mod     v1.0.0    Tentari    ↻
  cool_mod   v2.1.0    Community
```

The ↻ icon indicates the mod has an `update_url` and can be auto-updated.

#### `mod scan`
Security-scans all installed mods for dangerous patterns:

```
E ...> mod scan
  🔍 scanned 3 files  ✓ clean
```

If issues are found:
```
E ...> mod scan
  🔍 scanned 3 files  ⚠ 1 issues
    my_mod.py:42  eval(
```

#### `mod available`
List all mods available in the registry:

```
E ...> mod available
  📦 Available Mods (12 packages)
  cool_mod     v1.2.0    Adds swing rhythm       rhythm,swing
  bass_gen     v0.9.0    Bass line generator     bass,accompaniment
  ...
```

#### `mod fetch <name>`
Download and install a mod from the registry:

```
E ...> mod fetch cool_mod
  ⟳ downloading cool_mod
  [████████████████████] 100%
  ✓ saved  cool_mod.py (24KB)
```

The download includes progress bar and automatic security scan.

#### `mod update <name>`
Update a specific mod to the latest version:

```
E ...> mod update cool_mod
  ⟳ updating cool_mod
  ✓ saved  cool_mod.py (26KB)
```

#### `mod update --all`
Update all installed mods that have an `update_url`:

```
E ...> mod update --all
  ⟳ updating my_mod
  ✓ saved  my_mod.py (12KB)
    old_mod  (no update_url)
  ⟳ updating cool_mod
  ✓ saved  cool_mod.py (26KB)
```

#### `mod remove <name>`
Uninstall a mod:

```
E ...> mod remove old_mod
  🗑 removed  old_mod.py
```

---

### plugin Commands — Full Reference

| Subcommand | Description | Example |
|------------|-------------|---------|
| `list` | Show installed plugins | `plugin list` |
| `scan` | Security-scan all plugins | `plugin scan` |
| `available` | List plugins available in registry | `plugin avail` |
| `fetch <name>` | Download and install from registry | `plugin fetch viz` |
| `update <name>` | Update a specific plugin | `plugin update viz` |
| `update --all` | Update all plugins with update_url | `plugin update --all` |
| `remove <name>` | Uninstall a plugin | `plugin remove old_viz` |
| `version` | Show plugin system version | `plugin version` |

All subcommands work identically to `mod` but target the `plugins/` directory instead of `mods/`.

---

### Security System — AST-Based Static Analysis

Mod security uses **Python AST (Abstract Syntax Tree) analysis** — not string matching. This catches obfuscated calls that string-based scanning would miss.

#### What Gets Blocked

| Category | Examples | Why |
|----------|----------|-----|
| Dangerous function calls | `.system()`, `.popen()`, `.Popen()`, `.run()` | Shell/process execution |
| Dangerous builtins | `eval()`, `exec()`, `compile()`, `__import__()`, `open()` | Arbitrary code execution |
| Dynamic attribute access | `getattr(obj, 'system')`, `setattr()` | Obfuscated access to blocked functions |
| Dangerous dunders | `__import__`, `__subclasses__`, `__globals__`, `__builtins__`, `__code__` | Python internals exploitation |
| String obfuscation | `getattr(__builtins__, '__import__')('o'+'s')` | Bypass attempts via string concatenation |

String-based obfuscation **does not bypass** AST scanning. This code:

```python
getattr(__builtins__, '__import__')('o'+'s').system('calc')
```

Would be caught because the AST sees `getattr()` calls and `system()` attribute access regardless of how strings are constructed.

#### What Is NOT Blocked (Safe)

```
len(), range(), print(), str(), int(), list(), dict()
min(), max(), sum(), abs(), sorted(), enumerate()
Exception, ValueError, TypeError
api.add_command(), api.log(), api.on()
```

#### Restricted Execution Environment

When a mod passes the AST scan and is loaded, its `init()` function runs in a **restricted builtins environment**:

```python
RESTRICTED_BUILTINS = {
    'len': len, 'range': range, 'print': print,
    'str': str, 'int': int, 'list': list, 'dict': dict,
    # NO: __import__, open, eval, exec, compile,
    # NO: getattr, setattr, globals, locals
}
```

This means even if a mod passes the AST scan, it cannot import modules, read files, or execute system commands at runtime. **Plugins** (in `plugins/`) still have full access — only `mods/` are sandboxed.

#### Security Check on Download

When you use `mod fetch` or `mod update`, the downloaded file is scanned **before** being saved. If AST analysis finds dangerous patterns, the file is deleted and not installed:

```
E ...> mod fetch malware
  ⟳ downloading malware
  ✓ saved
  ✗ Security block — rejected
    line 3: call to .system
    line 5: getattr() — dynamic attribute access blocked
```

---

### Registry API Specification

The package manager can connect to any HTTP server that implements this API:

#### Endpoint: `GET /api`
Returns the full package list JSON:

```json
{
    "version": "2.0.0",
    "updated": "2024-12-25T12:00:00",
    "mods": { ... },
    "plugins": { ... }
}
```

#### Endpoint: `GET /api/{type}/{name}/download`
Returns the raw file bytes for a mod or plugin.

Default registry: `http://localhost:5592/api`

#### Setting a Custom Registry

```powershell
E ...> pkglist update url https://my-registry.example.com/api
```

The URL must return a JSON object with `mods` and `plugins` keys.

#### Registry URL Format

The URL can point to:
- A raw JSON file on any server (e.g., GitHub Gist, raw.githubusercontent.com)
- A dedicated API server
- A local file (using `file://` or `pkglist update file <path>`)

Example using GitHub:

```powershell
E ...> pkglist update url https://raw.githubusercontent.com/tentari/e-packages/main/pkglist.json
```

---

### Version Comparison

E uses semantic versioning (`MAJOR.MINOR.PATCH`). The `compare_versions()` function handles:
- Numeric comparison: `1.0.0` < `2.0.0`
- Pre-release tags: `1.0.0-alpha` < `1.0.0`
- Patch-level updates: `1.0.0` < `1.0.1`

Use `mod update --all` or `plugin update --all` to check for and install updates.

### Version Check Command

```powershell
E ...> pkglist version
```

Shows the package manager version (currently 2.0.0).

### Troubleshooting Package Manager

| Problem | Solution |
|---------|----------|
| `mod fetch` fails with HTTP error | Check the registry URL: `pkglist show`. The server may be down. |
| `mod list` shows nothing | You haven't installed any mods yet. Use `mod available` to see what's available. |
| `mod available` shows nothing | The pkglist is empty. Use `pkglist update url <url>` to load one. |
| Security scan false positive | Move the file from `mods/` to `plugins/` (plugins are not scanned). |
| Downloaded file is corrupted | The download may have been interrupted. Try `mod fetch <name>` again. |
| Plugin not appearing after install | Make sure the plugin file has a `register(api)` function. Check for Python errors in the console. |

---

### Complete Example — Building and Distributing a Plugin

Here's the end-to-end workflow for creating, packaging, and installing a plugin:

#### Step 1: Create the plugin

```python
# plugins/echo.py
"""Echo plugin — repeats what you type."""

def register(api):
    def echo(args):
        print("  " + " ".join(args))

    api.add_command("echo", echo, "Echo: echo <text>")
    api.log("  Echo plugin loaded!")
```

#### Step 2: Test it

```powershell
py -3 eshell.py
E ...> echo Hello World
  Hello World
```

#### Step 3: Package it as EZip

```python
# create_ezip.py
import zipfile, json, os

plugin_code = """def register(api):
    def echo(args):
        print("  " + " ".join(args))
    api.add_command("echo", echo, "Echo: echo <text>")
"""

manifest = {
    "name": "echo_plugin",
    "version": "1.0.0",
    "type": "plugin",
    "entry": "main.py",
    "author": "You",
    "description": "Simple echo command for eshell",
    "tags": ["utility", "echo"],
}

with zipfile.ZipFile("echo_plugin.ezip", "w") as zf:
    zf.writestr("EzPk", "EzPk")
    zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    zf.writestr("main.py", plugin_code)

print("Created echo_plugin.ezip")
```

#### Step 4: Distribute

Share `echo_plugin.ezip` or upload it to your registry server. Others install with:

```powershell
E ...> ezip install echo_plugin.ezip
```

Or if it's in a registry:

```powershell
E ...> plugin fetch echo_plugin
```

---

## 46. EZip Packages — Distribution Format

EZip is the standard package format for distributing mods, plugins, and other E extensions. An EZip file is a ZIP archive with a specific internal structure that E can verify, security-scan, and auto-install.

### EZip File Structure

```
my_extension.ezip
├── EzPk                      # Required — magic marker (empty or "EzPk")
├── manifest.json             # Required — package metadata (JSON)
├── main.py                   # Required — entry point (plugin/mod code)
├── assets/                   # Optional — supporting files
│   ├── config.json
│   └── template.e
└── requirements.txt          # Optional — pip dependencies
```

### manifest.json — Full Specification

```json
{
    "name": "echo_plugin",
    "version": "1.0.0",
    "type": "plugin",
    "entry": "main.py",
    "author": "Tentari",
    "description": "Simple echo command for eshell",
    "tags": ["utility", "echo"],
    "min_engine_version": "2.0.0",
    "max_engine_version": "3.0.0",
    "dependencies": ["numpy>=1.20"],
    "license": "MIT",
    "homepage": "https://github.com/tentari/e-echo",
    "update_url": "https://example.com/updates/echo.py",
    "eshell_help": "echo <text> — Repeats what you type"
}
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Package name (used for directory name on install) |
| `version` | Yes | string | Semantic version (e.g. `"1.0.0"`, `"2.3.1-beta"`) |
| `type` | Yes | string | `"mod"` or `"plugin"` |
| `entry` | Yes | string | Entry point filename (usually `"main.py"`) |
| `author` | No | string | Creator name or handle |
| `description` | No | string | Short description (shown in `pkglist search`) |
| `tags` | No | array of strings | Search keywords: `["rhythm", "waltz"]` |
| `min_engine_version` | No | string | Minimum E engine version required |
| `max_engine_version` | No | string | Maximum E engine version supported |
| `dependencies` | No | array of strings | Python pip dependencies: `["numpy>=1.20"]` |
| `license` | No | string | SPDX identifier: `"MIT"`, `"GPL-3.0"`, `"Apache-2.0"` |
| `homepage` | No | string | Project website URL |
| `update_url` | No | string | Direct URL for auto-updates (used by `mod update`) |
| `eshell_help` | No | string | Help text shown in eshell `help` |

### Creating an EZip Package

#### Method 1: Using the command line

```powershell
# Create the structure
mkdir ezip_workdir
cd ezip_workdir

# Create EzPk magic marker
echo EzPk > EzPk

# Create manifest.json
echo '{"name":"my_pack","version":"1.0.0","type":"mod","entry":"main.py","author":"You"}' > manifest.json

# Create the plugin/mod code
echo 'def init(api):' > main.py
echo '    api.add_command("mypack", lambda a: print("ok"), "My command")' >> main.py

# Zip it
tar -a -c -f ../my_pack.ezip *
cd ..
```

#### Method 2: Using Python

```python
# build_ezip.py
import zipfile, json, os

# Your plugin code
plugin_code = '''def register(api):
    def hello(args):
        print("  Hello from EZip!")
    api.add_command("hello", hello, "Say hello")
'''

# Manifest
manifest = {
    "name": "hello_plugin",
    "version": "1.0.0",
    "type": "plugin",
    "entry": "main.py",
    "author": "You",
    "description": "Hello world plugin",
    "tags": ["hello", "example"],
    "license": "MIT",
}

# Build the ezip
with zipfile.ZipFile("hello_plugin.ezip", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("EzPk", "EzPk")
    zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    zf.writestr("main.py", plugin_code)

print("Created hello_plugin.ezip")
```

#### Method 3: Using eshell's ezip command (if already installed)

```
E ...> ezip list existing_package.ezip    # See what's inside a working package
E ...> ezip info existing_package.ezip   # Inspect its manifest
```

### Installing EZip Packages

```powershell
# Install as a mod (default)
E ...> ezip install my_plugin.ezip

# Install explicitly as a plugin
E ...> ezip install my_plugin.ezip --plugin

# Preview contents before installing
E ...> ezip list unknown_package.ezip
  Contents of unknown_package.ezip:
  EzPk
  manifest.json
  main.py
  assets/help.txt

# Show metadata only
E ...> ezip info package.ezip
  Package: hello_plugin
  Version: 1.0.0
  Type: plugin
  Author: You
  Entry: main.py
```

### What Happens During Installation

When you run `ezip install package.ezip`:

1. **Magic check** — verifies the `EzPk` marker exists in the archive
2. **Manifest validation** — reads `manifest.json`, checks required fields
3. **Security scan** — scans all `.py` files for dangerous patterns
4. **Version check** — compares `min_engine_version`/`max_engine_version` against current E version
5. **Extraction** — extracts to `mods/<name>/` or `plugins/<name>/`
6. **Registration** — the mod/plugin is available immediately (no restart needed)

If any step fails, installation is aborted and no files are written.

### EZip vs Direct Drop-In

| Method | Pros | Cons |
|--------|------|------|
| **EZip install** | Security scan, manifest validation, version check, clean extraction | Requires creating the archive |
| **Direct drop-in** (copy `.py` to `mods/` or `plugins/`) | Fast, no packaging needed | No security validation, no metadata, no auto-update |

For development, use direct drop-in. For distribution, use EZip.

### Auto-Update Support

If your EZip's `manifest.json` includes an `update_url` field, users can auto-update:

```powershell
E ...> mod update my_mod              # Update specific mod
E ...> mod update --all               # Update all mods with update_url
E ...> plugin update my_plugin        # Update specific plugin
E ...> plugin update --all            # Update all plugins with update_url
```

The `update_url` should point directly to the latest `.py` file (not another EZip). E downloads it, security-scans it, and replaces the old file.

### EZip Registry Distribution

To make your EZip available through the package registry:

1. Upload the `.ezip` file to a web server
2. Add an entry to a `pkglist.json` registry:

```json
{
    "mods": {
        "my_mod": {
            "version": "1.0.0",
            "description": "My awesome mod",
            "author": "You",
            "tags": "utility,awesome",
            "url": "https://example.com/mods/my_mod.py"
        }
    }
}
```

3. Users install with:

```powershell
E ...> mod fetch my_mod
```

### Troubleshooting EZip

| Problem | Cause | Solution |
|---------|-------|----------|
| "missing EzPk" | The archive doesn't contain an EzPk marker | Add `EzPk` file to the ZIP root |
| "no manifest.json" | Missing metadata file | Create `manifest.json` in the ZIP |
| "security block" | Code contains dangerous patterns | Remove blocked patterns or distribute as plugin (not mod) |
| "name mismatch" | manifest.json name doesn't match filename | Fix the name field |
| Engine version conflict | `min_engine_version` > current E version | Update E or set a lower min version |

---

## 47. The Player (Console & GUI)

E has two built-in players:

### Console Player

```powershell
E ...> play song.mid
```

Shows a progress bar with elapsed/total time. Controls while playing:

| Key | Action |
|-----|--------|
| `←` | Go back 5 seconds |
| `→` | Skip forward 5 seconds |
| `↑` | Volume up 10% |
| `↓` | Volume down 10% |
| `Space` | Pause / Resume |
| `q` or `Esc` | Quit |

### GUI Player (Glassmorphism)

```powershell
E ...> play song.mid --gui
```

A transparent, glass-like window with:
- Play/Pause button
- Progress slider
- Volume control
- Song title display
- Elapsed / remaining time

### Player Session Examples

```powershell
# Simple playback
E ...> play nocturne.mid

# Play with GUI
E ...> play symphony.mid --gui

# Play a project (compiles first)
E ...> play sonata/index.ei

# Play an album
E ...> play album.enx

# Play a mixed-mode file
E ...> play piece.eci

# Play audio directly (no MIDI involved)
E ...> play recording.wav
E ...> play song.mp3

# Quick compile + play in one step
E ...> play song.e               # Compiles to .mid, then plays
```

### Using Player from CLI (without eshell)

```powershell
py -3 ep.py play nocturne.ei       # Compile project + play
py -3 player.py album.enx           # Play album directly
py -3 player.py song.mid --gui      # GUI mode from CLI
```

### Play Any Format

The player handles `.e`, `.ei`, `.eci`, `.enx`, `.eic`, `.ec`, `.mid`, `.wav`, `.mp3`:

```powershell
E ...> play song.e           # Compile then play
E ...> play song.ei          # Compile project then play
E ...> play song.eci         # Compile mixed-mode file then play
E ...> play album.enx        # Compile full album then play
E ...> play song.wav         # Play audio directly
E ...> play song.mp3         # Play compressed audio
```

---

## 48. Troubleshooting

### "No module named mido"

```powershell
pip install mido
```

### "No module named numpy"

```powershell
pip install numpy scipy
```

### "Audio not playing"

1. Check your speakers/headphones
2. Try a different audio device: `audio devices` → `audio set-device N`
3. Make sure your MIDI synthesizer is working (on Windows: "Microsoft GS Wavetable Synth")

### "Arrow keys don't work during playback"

Some terminals eat arrow key events. Try:
- Windows Terminal instead of old cmd.exe
- PowerShell 7 instead of Windows PowerShell

### "UnicodeEncodeError"

Set the environment variable before running:

```powershell
set PYTHONIOENCODING=utf-8
```

### "Compile is slow for large files"

Use `.ec` format for instant loading:

```powershell
E ...> compile huge_song.e -o huge_song.ec   # Pre-compile once
E ...> compile huge_song.ec -o huge_song.mid  # Fast compilation
```

### "Notes sound muddy / too much reverb"

E automatically kills reverb (CC91) and chorus (CC93) on all 16 MIDI channels. If you still hear ambience, your MIDI synth may have built-in effects — check your sound settings.

### "ep.py import says 'Unknown format'"

Make sure the file extension is one of: `.mid`, `.midi`, `.wav`, `.mp3`, `.mp4`, `.m4a`, `.mov`, `.flac`, `.ogg`, `.aac`, `.ec`. For audio files, ensure FFmpeg is installed.

### "The .enx file compiles but is silent"

Check that each `.ei` file in the `order` directives actually exists and has notes. Use `info` to verify:

```powershell
E ...> info movement1/index.ei     # Should show Events > 0
```

### "Inheritance doesn't seem to work"

1. Make sure the `root` path in the child `.ei` is **relative to the child file's directory**, not the current working directory
2. Check for circular inheritance (A → B → A) — this is blocked
3. Verify the parent file exists: `root "../orchestra_base.ei"` — the `..` goes up from the child's folder

### "The .eci file isn't switching modes"

Make sure `@mode` is at the **start of the line** with no leading spaces:

```
@mode machine     # ✓ Correct
  @mode human     # ✗ Wrong — leading space breaks detection
```

### "convert song.mid --project created an empty project"

Some MIDI files use note_on/note_off pairs across different tracks in unexpected ways. Try:

```powershell
E ...> convert song.mid -o song.e          # Single file first
E ...> info song.e                         # Check if notes were found
```

If the MIDI file has 0 notes, it might use a non-standard format or have tempo changes that confused the parser.

### "I get a 'circular reference' error in inheritance"

You have a loop: A → B → C → A. Break the chain by removing one of the `root` directives.

### "FFmpeg not found for audio import"

Install FFmpeg:
- Windows: Download from gyan.dev or use `winget install ffmpeg`
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### "The player crashes on startup"

Try running without the GUI first:

```powershell
py -3 player.py song.mid           # No GUI — works on all systems
```

If the console player also crashes, the MIDI file might be corrupted. Try recompiling:

```powershell
E ...> compile song.e -o song.mid --force
```

---

## 49. Command Reference

This section documents every command across all E tools: eshell (interactive shell), ep.py (command-line compiler), player.py (playback), and auxiliary scripts.

### How to Start Each Tool

| Tool | Command | Description |
|------|---------|-------------|
| **eshell** (interactive) | `py -3 eshell.py` | Full-featured shell with all commands |
| **ep.py** (CLI) | `py -3 ep.py <command> [args]` | Direct command-line interface |
| **player.py** (playback) | `py -3 player.py <file> [--gui]` | Audio/MIDI player |
| **ai.py** (AI helper) | `py -3 ai.py` | AI-assisted composition tools |

---

### eshell Commands (Full Reference)

Run `py -3 eshell.py` to start the interactive shell, then use these commands:

#### `cd <directory>`
Change the current working directory.

```
E ...> cd examples         # Go into examples folder
E ...> cd ..               # Go up one level
E ...> cd /absolute/path   # Go to absolute path
```

#### `ls [directory]`
List files in current or specified directory. Color-coded by type:
- Green: `.e`, `.ei`, `.eic` (source files)
- Yellow: `.mid`, `.wav`, `.mp3`, `.mp4` (playable files)
- Red: `.ee`, `.ec`, `.ecc` (binary/encrypted)
- Magenta: `.py` (Python scripts)
- Cyan: Directories

```
E ...> ls
E ...> ls my_project/
```

#### `compile <file> [-o <out>] [--human] [--machine] [--volume N]`
Compile any E source file to an output format. Auto-detects input format.

| Flag | Description |
|------|-------------|
| `-o <file>` | Output file path (default: input name + .mid) |
| `--human` | Convert MACHINE tokens to HUMAN syntax in `.eic` |
| `--machine` | Convert HUMAN syntax to MACHINE tokens |
| `--volume N` | Override master volume (0.0–1.0) |

**Examples:**
```
E ...> compile song.e -o song.mid        # .e → MIDI
E ...> compile song.e -o song.wav        # .e → WAV audio
E ...> compile song.e -o song.mp3        # .e → MP3
E ...> compile song.e -o song.mp4        # .e → video
E ...> compile song.e -o song.ec         # .e → compiled binary
E ...> compile song.e -o song.eic        # .e → clear bundle
E ...> compile project.ei -o song.mid    # .ei project → MIDI
E ...> compile project.ei -o project.eic # .ei → bundle
E ...> compile mixed.eci -o song.mid     # .eci → MIDI
E ...> compile album.enx -o album.mid    # .enx album → MIDI
E ...> compile song.e -o song.eic --human  # Convert to HUMAN syntax
```

#### `convert <input> [-o <output>] [--project]`
Convert between formats — primarily for IMPORTING (MIDI/audio → E).

| Flag | Description |
|------|-------------|
| `-o <file>` | Output file path |
| `--project` | Import as full `.ei` project with parts/ directory |

**Examples:**
```
E ...> convert song.mid -o song.e              # MIDI → human-readable .e
E ...> convert song.mid --project              # MIDI → full project (index.ei + parts/)
E ...> convert song.ec -o song.e              # Compiled binary → .e
E ...> convert recording.wav -o song.e         # Audio transcription → .e
E ...> convert song.mp3 -o song.e              # MP3 → .e
E ...> convert video.mp4 -o song.e             # Video → .e
```

#### `play <file> [--gui]`
Play any supported file through the MIDI synthesizer or audio driver.

| Flag | Description |
|------|-------------|
| `--gui` | Open glassmorphism GUI player instead of console |

**Examples:**
```
E ...> play song.mid            # Play MIDI file
E ...> play song.e              # Compile .e to MIDI then play
E ...> play song.ei             # Compile project then play
E ...> play album.enx           # Compile album then play
E ...> play song.mid --gui      # Play in GUI window
E ...> play song.wav            # Play audio directly
E ...> play song.mp3            # Play MP3 directly
```

#### `gui <file>`
Alias for `play <file> --gui` — play in glassmorphism window.

```
E ...> gui nocturne.mid
E ...> gui symphony.ei
```

#### `info <file>`
Show file statistics: number of events, BPM, duration, note range.

```
E ...> info Rush_E.e
File: Rush_E.e
Events: 19853
BPM: 270.0
Duration: 174.23s
Note range: 21-108
```

Works with: `.e`, `.ei`, `.eci`, `.enx`, `.eic`, `.ec`, `.mid`

#### `sign <file> [--embed] [--force]`
Sign a file with your author name and social links. Uses HMAC-SHA256.

| Flag | Description |
|------|-------------|
| `--embed` | Embed signature inside the file (for `.eic`, `.ec`, `.ee`, `.ecc`) |
| `--force` | Overwrite existing signature |

```
E ...> sign song.eic
Author> Tentari
Instagram> @tentari
Discord> pixelhollow
✓ Signed
```

#### `encrypt <file> [-o <out.ee>]`
Encrypt a file with AES-256-GCM. Supports single files or `.ei` project bundles.

```
E ...> encrypt song.e -o song.ee             # Encrypt single file
E ...> encrypt project.ei -o project.ee      # Bundle + encrypt project
E ...> encrypt project.ee -o song.mid        # Decrypt + compile
```

#### `ecc <file> [-o <out.ecc>]`
Compile + encrypt in one step. Takes `.e` → compiles to `.ec` → encrypts to `.ecc`.

```
E ...> ecc song.e -o song.ecc       # Compile then encrypt
```

#### `mod <subcommand> [args]`
Manage mods (Python files in `mods/` directory).

| Subcommand | Description | Example |
|------------|-------------|---------|
| `list` | List installed mods | `mod list` |
| `available` | List available in registry | `mod avail` |
| `scan` | Security-scan all mods | `mod scan` |
| `update <name>` | Update a specific mod | `mod update mymod` |
| `fetch <name>` | Download and install from registry | `mod fetch cool-plugin` |
| `remove <name>` | Uninstall a mod | `mod remove old-mod` |
| `version` | Show mod system version | `mod version` |

#### `plugin <subcommand> [args]`
Manage plugins (Python files in `plugins/` directory).

| Subcommand | Description | Example |
|------------|-------------|---------|
| `list` | List installed plugins | `plugin list` |
| `available` | List available in registry | `plugin avail` |
| `scan` | Security-scan all plugins | `plugin scan` |
| `update <name>` | Update a specific plugin | `plugin update myplugin` |
| `fetch <name>` | Download and install from registry | `plugin fetch viz` |
| `remove <name>` | Uninstall a plugin | `plugin remove old-plugin` |
| `version` | Show plugin system version | `plugin version` |

#### `pkglist <subcommand> [args]`
Manage the package registry (central list of available mods/plugins).

| Subcommand | Description | Example |
|------------|-------------|---------|
| `show` | Show current registry URL | `pkglist show` |
| `update url <url>` | Set registry URL | `pkglist update url http://...` |
| `search <term>` | Search packages by name | `pkglist search rush` |
| `version` | Show package list version | `pkglist version` |
| `detail <name>` | Show package details | `pkglist detail cool-mod` |

#### `ezip <subcommand> <file>`
Install and inspect EZip packages.

| Subcommand | Description | Example |
|------------|-------------|---------|
| `install` | Install an `.ezip` package | `ezip install plugin.ezip` |
| `list` | List contents of an `.ezip` file | `ezip list package.ezip` |
| `info` | Show package metadata | `ezip info package.ezip` |

#### `gc [strategy]`
View or change garbage collection strategy.

| Strategy | Description |
|----------|-------------|
| `default` | Dedup, range check, zero-duration removal |
| `aggressive` | Also merges overlapping same-pitch notes |
| `off` | Disable GC |

```
E ...> gc                   # Show current strategy
E ...> gc aggressive        # Switch to aggressive
E ...> gc default           # Back to default
```

#### `audio <subcommand> [args]`
Configure audio output devices.

| Subcommand | Description | Example |
|------------|-------------|---------|
| `devices` | List all audio output devices | `audio devices` |
| `set-device N` | Set active device by number | `audio set-device 2` |
| `config` | Show current audio configuration | `audio config` |

#### `clear`
Clear the terminal screen and redisplay the banner.

```
E ...> clear
```

#### `exit` / `quit`
Exit the E shell.

```
E ...> exit
```

---

### ep.py CLI (Direct Command Line)

Run directly from your terminal without entering the interactive shell.

#### `py -3 ep.py compile <input> -o <output> [--volume N] [--bpm N]`
Compile any input to any output format.

| Flag | Description |
|------|-------------|
| `-o <file>` | Output path (required) |
| `--volume N` | Master volume override (0.0–1.0) |
| `--bpm N` | Override detected BPM |
| `--effects key=val` | Audio effects parameters (key=val,key=val) |

```
py -3 ep.py compile song.e -o song.mid
py -3 ep.py compile song.e -o song.wav --volume 0.8
py -3 ep.py compile project.ei -o project.mid
py -3 ep.py compile album.enx -o album.mid
```

#### `py -3 ep.py play <file>`
Compile (if needed) and play a file directly.

```
py -3 ep.py play song.mid
py -3 ep.py play song.e          # Compiles then plays
py -3 ep.py play album.enx       # Compiles album then plays
```

#### `py -3 ep.py info <file>`
Show file statistics without entering eshell.

```
py -3 ep.py info Rush_E.e
py -3 ep.py info project.enx
```

#### `py -3 ep.py import <input> -o <output> [--project]`
Import MIDI, audio, or `.ec` files to E source.

| Flag | Description |
|------|-------------|
| `-o <file>` | Output path (`.e` file or directory with `--project`) |
| `--project` | Create full `.ei` project with parts/ directory |

```
py -3 ep.py import song.mid -o song.e              # MIDI → .e
py -3 ep.py import song.mid --project              # MIDI → full project
py -3 ep.py import song.ec -o song.e               # Compiled → .e
py -3 ep.py import recording.wav -o song.e         # Audio → .e
```

---

### player.py (Playback)

The standalone player can be called directly without eshell.

#### `py -3 player.py <file> [--gui]`

| Flag | Description |
|------|-------------|
| `--gui` | Launch glassmorphism GUI window |

```
py -3 player.py song.mid                   # Console player
py -3 player.py song.mid --gui             # GUI player
py -3 player.py song.e                     # Compile + play
py -3 player.py album.enx                  # Compile album + play
py -3 player.py song.wav                   # Play audio file
```

**Keyboard Controls (Console Player):**

| Key | Action |
|-----|--------|
| `←` | Seek backward 5 seconds |
| `→` | Seek forward 5 seconds |
| `↑` | Volume +10% |
| `↓` | Volume –10% |
| `Space` | Pause / Resume |
| `q` or `Esc` | Quit |

---

### Standalone Tools

#### `py -3 ai.py`
Launch the AI composition assistant (experimental). Generates music from text prompts.

#### `py -3 tools/e2midi.py <input.e> -o <output.mid>`
Legacy E → MIDI converter. Use `eshell compile` instead for new projects.

```
py -3 tools/e2midi.py song.e -o song.mid
```

#### `py -3 tools/midi2e.py <input.mid> -o <output.e>`
Legacy MIDI → E converter. Use `eshell convert` or `ep.py import` instead.

```
py -3 tools/midi2e.py song.mid -o song.e
```

#### `py -3 tools/dl_fluidsynth.py`
Download and install FluidSynth soundfont for higher-quality audio rendering.

---

### Complete Conversion Matrix

| Input | → Output | Tool / Command |
|-------|----------|---------------|
| `.e` | `.mid` | `eshell compile` or `ep.py compile` |
| `.e` | `.wav` | `eshell compile` |
| `.e` | `.mp3` | `eshell compile` |
| `.e` | `.mp4` | `eshell compile` |
| `.e` | `.ec` | `eshell compile` |
| `.e` | `.eic` | `eshell compile` |
| `.e` | `.ee` | `eshell encrypt` or `ep.py compile -o .ee` |
| `.e` | `.ecc` | `eshell ecc` |
| `.ei` | `.mid` | `eshell compile` |
| `.ei` | `.eic` | `eshell compile` |
| `.ei` | `.ee` (bundle) | `eshell encrypt` |
| `.eci` | `.mid` | `eshell compile` |
| `.enx` | `.mid` | `eshell compile` |
| `.enx` | `.eic` | `eshell compile` — bundles full album |
| `.enx` | `.wav` | `eshell compile` |
| `.enx` | `.mp3` | `eshell compile` |
| `.enx` | `.mp4` | `eshell compile` |
| `.enx` | `.ee` | `eshell encrypt` — encrypts full album |
| `.mid` | `.e` | `eshell convert` or `ep.py import` |
| `.mid` | `.ei` project | `eshell convert --project` or `ep.py import --project` |
| `.ec` | `.e` | `eshell convert` or `ep.py import` |
| `.eic` | `.mid` | `eshell compile` |
| `.eic` | `.ee` | `eshell encrypt` |
| `.ee` | `.mid` | `eshell compile` (decrypts then compiles) |
| `.ecc` | `.mid` | `eshell compile` (decrypts then compiles) |
| `.wav` | `.e` | `eshell convert` or `ep.py import` |
| `.mp3` | `.e` | `eshell convert` or `ep.py import` |
| `.mp4` | `.e` | `eshell convert` or `ep.py import` |
| `.mov` | `.e` | `eshell convert` |
| `.flac` | `.e` | `eshell convert` |
| `.ogg` | `.e` | `eshell convert` |
| `.aac` | `.e` | `eshell convert` |
| `.m4a` | `.e` | `eshell convert` |
| `.aiff` | `.e` | `eshell convert` |
| `.wma` | `.e` | `eshell convert` |

### Quick Syntax — Shortest Paths

| I want to… | Command |
|------------|---------|
| Hear a file | `play song.mid` |
| See file stats | `info song.e` |
| Turn MIDI into E | `convert song.mid -o song.e` |
| Turn MIDI into a project | `convert song.mid --project` |
| Turn audio into E | `convert recording.wav -o song.e` |
| Compile to MIDI | `compile song.e -o song.mid` |
| Compile to audio | `compile song.e -o song.wav` |
| Share a project as one file | `compile project.ei -o project.eic` |
| Encrypt my work | `encrypt song.e -o song.ee` |
| Sign my work | `sign song.eic` |
| List audio devices | `audio devices` |
| Install a mod | `ezip install my_mod.ezip` |
| Clear the screen | `clear` |
| Quit | `exit` | |

---

## 50. For AI Agents — How to Compose Music with E

This section is specifically for **AI language models, agents, and automated composition tools** that generate E language output. If you are a human composer, you can skip this — but reading it will help you understand how AI should think about your music.

### Core Principles for AI Composition

1. **Music has structure.** Random notes are not music. Every composition needs:
   - A key (tonal center) — set with `@key` or implicit in your note choices
   - A tempo — set with `@bpm`
   - A dynamic arc — quiet parts, loud parts, transitions
   - Rhythmic consistency — patterns that repeat and evolve
   - An ending — music doesn't just stop, it resolves

2. **Less is more.** A simple melody with good rhythm beats a chaotic wall of notes. Start simple, add complexity where it serves the music.

3. **Use the right format for the job:**
   - `#MACHINE` mode for precise, algorithmic, or AI-generated sequences
   - `#HUMAN` mode for readable, musical phrases
   - `.eci` when you want to mix both
   - `.ei` projects for multi-part compositions
   - `.enx` for sequencing multiple pieces into an album

4. **Respect musical ranges.**
   - Bass: MIDI 24–48 (C1–C3) — left hand, foundation
   - Mid: MIDI 48–72 (C3–C5) — melody, harmony
   - High: MIDI 72–96 (C5–C7) — upper extensions, glitter
   - Extreme low (below 24) and extreme high (above 96): use sparingly

### Step-by-Step AI Composition Flow

```
1. Choose a key and scale
   → @key A_minor  or  @scale C_Major

2. Set the tempo
   → @bpm 120  or  @adagio

3. Define the structure
   → section "Verse" { ... }
   → section "Chorus" { ... }
   → section "Bridge" { ... }

4. Write the harmony (chord progression)
   → Chord block in v2, or simultaneous T0 notes in machine
   → Common: I–V–vi–IV, ii–V–I, I–IV–I–V

5. Write the bass line (foundation)
   → Root notes of each chord, simple rhythm
   → Layer with percussion on channel 10 if desired

6. Write the melody (the tune people remember)
   → Mostly stepwise motion (notes close together)
   → Occasional leaps for emphasis
   → Follow the chord tones (root, third, fifth)

7. Add dynamics
   → Not all notes at V0.8 — vary it!
   → pp for quiet parts, ff for climax, crescendos between

8. Add articulations
   → Staccato for energy
   → Legato for smoothness
   → Accents on important beats

9. End properly
   → Return to the tonic (key center)
   → Slow down (ritardando) or hold a final chord
```

### Musical Rules AI Must Follow

#### Rule 1: Notes Must Fit the Key

If you set `@key C_Major`, every note should be in the C major scale (C, D, E, F, G, A, B). Accidentals (sharps/flats outside the key) are allowed for flavor but must resolve quickly.

If you're not using `@scale quantization`, you must ensure notes are in key yourself. Reference:

```
C_Major:  C  D  E  F  G  A  B    (no sharps/flats)
G_Major:  G  A  B  C  D  E  F#   (one sharp: F#)
D_Major:  D  E  F# G  A  B  C#   (two sharps: F#, C#)
A_Major:  A  B  C# D  E  F# G#   (three sharps)
E_Major:  E  F# G# A  B  C# D#   (four sharps)
F_Major:  F  G  A  Bb C  D  E    (one flat: Bb)

A_minor:  A  B  C  D  E  F  G    (no sharps/flats — same as C major)
D_minor:  D  E  F  G  A  Bb C    (one flat: Bb)
E_minor:  E  F# G  A  B  C  D    (one sharp: F#)
```

#### Rule 2: Voice Leading Matters

When chords change, each note should move as little as possible:

```
Bad voice leading (jumpy):
C4 → G4 → E4 → B4    (each note jumps by a large interval)

Good voice leading (smooth):
C4 → B3 → C4 → B3    (notes stay close, stepwise motion)
```

The ideal: each voice moves by 0–2 semitones when the chord changes.

#### Rule 3: Bass and Melody Are Different

- **Bass** plays root notes of chords, mostly on beats 1 and 3
- **Melody** plays higher, more active, on and off beats
- Don't put the melody in the bass register or vice versa

```
Bass (channel 0, MIDI 36-48):
T0 N36 D1000 V0.7       # C2 — root
T1000 N43 D1000 V0.7    # G2 — fifth
T2000 N36 D1000 V0.7    # C2 — root
T3000 N40 D1000 V0.7    # E2 — third

Melody (channel 1, MIDI 60-84):
T0 N60 D500 V0.8        # C4 — root
T500 N64 D250 V0.8      # E4 — third
T750 N67 D250 V0.8      # G4 — fifth
T1000 N72 D1000 V0.85   # C5 — octave
```

#### Rule 4: Use Channels Appropriately

| Channel | Use For | MIDI Range |
|---------|---------|------------|
| 0 | Piano (main instrument) | Full range |
| 1 | Accompaniment / backing | 48–72 |
| 2 | Bass | 24–48 |
| 9 | Guitar / plucked | 48–84 |
| 10 | Drums (special — see below) | See drum map |
| 11–15 | Orchestral (strings, brass, winds) | As appropriate |

#### Rule 5: Drum Channel (10) Note Map

Channel 10 is special — each MIDI number is a different drum:

| MIDI | Drum | Use |
|------|------|-----|
| 36 | Kick drum | Beat 1 (and 3 in 4/4) |
| 38 | Snare drum | Beats 2 and 4 |
| 42 | Closed hi-hat | Eighth notes |
| 46 | Open hi-hat | Accented beats |
| 49 | Crash cymbal | Section transitions |
| 51 | Ride cymbal | Steady pulse |
| 39 | Clap | Accents, fills |

Basic rock beat:
```
CH[10] T0 N36 D100 V0.9     # Kick
CH[10] T0 N42 D100 V0.7     # Hi-hat
CH[10] T250 N38 D100 V0.8   # Snare
CH[10] T250 N42 D100 V0.7   # Hi-hat
CH[10] T500 N36 D100 V0.9   # Kick
CH[10] T500 N42 D100 V0.7   # Hi-hat
CH[10] T750 N38 D100 V0.8   # Snare
CH[10] T750 N42 D100 V0.7   # Hi-hat
```

#### Rule 6: Dynamics Tell the Story

Music without dynamic variation is flat and lifeless. Follow this emotional arc:

```
Intro:    pp  (soft, mysterious)
Verse:    mp  (medium soft, building)
Chorus:   f   (loud, release)
Bridge:   p   (soft again, contrast)
Final Chorus: ff  (loudest, climax)
Outro:    pp  (fade away)
```

Velocity mapping:

| Dynamic | MIDI Velocity | E Code |
|---------|--------------|--------|
| ppp (barely audible) | 16 | `@vel:ppp` or `V0.13` |
| pp (very soft) | 33 | `@vel:pp` or `V0.26` |
| p (soft) | 49 | `@vel:p` or `V0.39` |
| mp (medium-soft) | 64 | `@vel:mp` or `V0.50` |
| mf (medium) | 80 | `@vel:mf` or `V0.63` |
| f (loud) | 96 | `@vel:f` or `V0.76` |
| ff (very loud) | 112 | `@vel:ff` or `V0.88` |
| fff (maximum) | 126 | `@vel:fff` or `V0.99` |

#### Rule 7: Structure Is Not Optional

Every piece needs a beginning, middle, and end. Use `.ei` sections:

```
section "Intro" { ... }        // Establishes mood, key, tempo
section "Verse" { ... }        // Presents the main material
section "Chorus" { ... }       // The memorable part, louder
section "Bridge" { ... }       // Contrast — different key or feel
section "Outro" { ... }        // Returns to tonic, fades
```

### What AI Should Generate vs Not Generate

| Task | Do This | Don't Do This |
|------|---------|---------------|
| Original composition | Create a `.e` or `.ei` with proper structure and dynamics | Dump 10,000 random notes at max velocity |
| Arrangement of existing work | Credit the original composer in the `composer` field | Claim the arrangement as fully original |
| Music in a specific style | Research the style's typical chords, rhythms, and dynamics | Copy a specific existing song's MIDI data |
| Responding to user request | Ask clarifying questions about mood, tempo, complexity | Generate without understanding the user's intent |
| Large-scale work | Use `.ei` project with parts/ directory | Put everything in one monolithic file |
| Teaching music | Use `#HUMAN` syntax and add comments | Use opaque machine tokens without explanation |

### AI Composition Templates

#### Template 1: Simple Piano Piece (Single .e file)

```
@bpm 120
@key C_Major

// Intro
play note(C4) @dur:h @vel:mp
play note(E4) @dur:h @vel:mp
play note(G4) @dur:h @vel:mp

// Verse melody
play note(C4) @dur:q @vel:mf
play note(D4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(F4) @dur:q @vel:mf
play note(G4) @dur:h @vel:f
play note(A4) @dur:q @vel:mf
play note(G4) @dur:q @vel:mf
play note(F4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(D4) @dur:h @vel:mp
play note(C4) @dur:w @vel:pp

// Chorus
play note(C4) @dur:q @vel:f
play note(E4) @dur:q @vel:f
play note(G4) @dur:q @vel:f
play note(C5) @dur:h @vel:ff
play note(B4) @dur:q @vel:f
play note(G4) @dur:q @vel:f
play note(E4) @dur:q @vel:f
play note(C4) @dur:w @vel:mp
```

#### Template 2: Multi-Movement Project (.ei + parts/)

**index.ei:**
```
project "AI Sonata in G"
composer "AI Assistant"
tempo 120

include "parts/melody.e" as melody
include "parts/bass.e" as bass

section "I. Allegro" {
    tempo 140
    play bass
    play melody after 2000ms
}

section "II. Adagio" {
    tempo 60
    play melody
    play bass after 1000ms
}
```

**parts/bass.e:**
```
@bpm 140
@key G_Major
T0 N43 D1000 V0.7      // G2
T1000 N47 D500 V0.7    // B2
T1500 N50 D500 V0.7    // D3
T2000 N43 D1000 V0.7   // G2
```

**parts/melody.e:**
```
@bpm 140
@key G_Major
play note(G4) @dur:q @vel:mf
play note(B4) @dur:e @vel:f
play note(D5) @dur:e @vel:f
play note(G5) @dur:h @vel:ff
```

#### Template 3: Album (.enx)

```
#ENX v1
project "AI-Generated Piano Suite"
composer "AI (guided by Human)"

order "movements/mvmt1.ei"
order "movements/mvmt2.ei" at 3000ms tempo 80
order "movements/mvmt3.ei" at 2000ms tempo 180
order "movements/mvmt4.ei" at 4000ms tempo 60
```

### Common Mistakes AI Makes (and How to Fix Them)

| Mistake | Why It's Bad | How to Fix |
|---------|-------------|------------|
| All notes at velocity 0.8 | No dynamic contrast, sounds robotic | Vary velocity: pp–mf–ff–pp |
| Every note starts at T0 | Dense cluster, no rhythm | Space notes out: T0, T250, T500, T750 |
| Only white keys in "minor key" | Minor keys need the raised 7th (G# in A minor) | Use proper harmonic minor: A B C D E F G# |
| Never returning to the tonic | Music feels unresolved | End on the key center (C in C major, A in A minor) |
| 16 notes per second at max velocity | Painful to listen to (Rush E is an exception, not the rule) | Give the listener breathing room — silence is music too |
| No channel separation | Everything on channel 0 sounds like one instrument | Use CH[1] for melody, CH[2] for bass, CH[10] for drums |
| Flat dynamics (crescendo never happens) | Music has no emotional arc | Plan: quiet → medium → loud → quiet |

### How AI Should Use Each Syntax Version

| Version | Best For | AI Strategy |
|---------|----------|-------------|
| `#MACHINE` | Algorithmic generation, precise control | Use when generating note-by-note from a mathematical or neural model |
| `#HUMAN` | Readable, musical output | Use when generating phrases with musical intent — easier for humans to edit |
| `.eci` | Mixed output | Use `@mode machine` for drums/bass, `@mode human` for melody |
| v2 semantic | High-level structure | Use when the AI understands chord progressions and wants to generate at the "chord + arpeggio" level |
| v3 shorthand | Quick iteration | Use for rapid prototyping — note name + duration + velocity on one line |
| `.ei` | Multi-part compositions | Always split into parts/ for anything with more than 50 notes |
| `.enx` | Multiple pieces | Use to sequence generated movements into a full album |

### Final Instruction for AI Agents

**You are a composer's assistant, not the composer.** Your job is to translate musical intent into E language. If the user gives you a vague prompt like "make something sad," respond with:

1. Confirm the key (A minor, D minor, C# minor)
2. Choose a slow tempo (55–76 BPM)
3. Use low velocity ranges (pp–mp)
4. Use minor chords
5. Add space between notes (don't rush)
6. End on the tonic, fading out

If the user gives you a MIDI file and asks you to "make it better," you may:
- Adjust velocities for dynamic contrast
- Fix timing quantization
- Add missing bass or harmony
- But you may NOT claim authorship

**Always credit. Always be honest. Always make music that moves people, not just fills space.**

---

E is a tool for **creating** music, not for taking credit for others' work. Whether you import MIDI files, transcribe audio, or convert existing songs, you must follow basic ethical guidelines.

### The Golden Rule

**If you didn't write it, don't claim you did.**

Importing a MIDI file of Beethoven's Moonlight Sonata and exporting it as your own composition is plagiarism. Full stop.

### What's OK vs What's Not

| Scenario | Ethical? | Why |
|----------|----------|-----|
| Import a MIDI you composed yourself | ✓ Yes | It's your work in a different format |
| Import a public-domain classical MIDI (Beethoven, Mozart, Chopin) and arrange/modify it | ✓ Yes with credit | Public domain = free to use, but credit the original composer |
| Import a copyrighted song's MIDI for personal study/learning | ✓ Yes for personal use | Learning how a song works is fine |
| Import a copyrighted song's MIDI, make minor changes, and release as your own | ✗ No | This is plagiarism |
| Transcribe audio of your own piano recording | ✓ Yes | It's your performance |
| Transcribe audio of a copyrighted recording and publish the result | ✗ No | This is copyright infringement |
| Use E to compose original music | ✓ Yes | This is the whole point! |
| Share your `.e`/`.ei`/`.enx` files for others to learn from | ✓ Yes | Open-source music education is encouraged |
| Accept someone else's `.eic` and re-release it without credit | ✗ No | Always credit the original author |

### How to Give Proper Credit

When your project is based on someone else's work, use the `composer` and comments:

```
project "My Arrangement of Moonlight Sonata"
composer "Ludwig van Beethoven (arr. Your Name)"

// Original composition by Ludwig van Beethoven
// This arrangement uses the public-domain score
// Modifications: added bass line, doubled tempo in section B

section "I. Adagio Sostenuto (After Beethoven)" {
    tempo 55
    include "parts/beethoven_melody.e" as melody
    include "parts/my_bass.e" as bass
    play melody with bass
}
```

### When Using MIDI Imports

Every MIDI file you import with `convert song.mid --project` creates an `index.ei` that you should edit to add proper attribution:

```
project "Imported Piece"
composer "Original Composer"     // ← CHANGE THIS to the real composer

// Source: name_of_song.mid — downloaded from [source]
// Converted to E on [date]
// I did not compose this. All credit to the original creator.
```

### Plagiarism Detection

E files can be signed (`sign` command) with the author's name and social links. If you find an unsigned `.eic` or `.e` file that matches a known composition without credit:

1. Check if it's signed (`info file.eic` shows the author if signed)
2. Compare against the original to see if meaningful changes were made
3. If it's clearly a copy without credit, call it out

### Educational Use

Importing songs to **learn** how they work is encouraged. Import Beethoven to see how he constructed a sonata. Import a pop song to study its chord progression. Just don't publish the result as your own work.

```
// Educational analysis of [Song Name]
// I imported this to study the chord progression
// Not for publication — personal learning only
```

### Sign Your Work

Always sign your original compositions so people know it's yours:

```powershell
E ...> sign my_song.eic
Author> Your Name
Instagram> @yourhandle
✓ Signed
```

---

## 51. Ethics & Attribution — Don't Steal Music

E is a tool for **creating** music, not for taking credit for others' work. Whether you import MIDI files, transcribe audio, or convert existing songs, you must follow basic ethical guidelines.

### The Golden Rule

**If you didn't write it, don't claim you did.**

Importing a MIDI file of Beethoven's Moonlight Sonata and exporting it as your own composition is plagiarism. Full stop.

### What's OK vs What's Not

| Scenario | Ethical? | Why |
|----------|----------|-----|
| Import a MIDI you composed yourself | ✓ Yes | It's your work in a different format |
| Import a public-domain classical MIDI (Beethoven, Mozart, Chopin) and arrange/modify it | ✓ Yes with credit | Public domain = free to use, but credit the original composer |
| Import a copyrighted song's MIDI for personal study/learning | ✓ Yes for personal use | Learning how a song works is fine |
| Import a copyrighted song's MIDI, make minor changes, and release as your own | ✗ No | This is plagiarism |
| Transcribe audio of your own piano recording | ✓ Yes | It's your performance |
| Transcribe audio of a copyrighted recording and publish the result | ✗ No | This is copyright infringement |
| Use E to compose original music | ✓ Yes | This is the whole point! |
| Share your `.e`/`.ei`/`.enx` files for others to learn from | ✓ Yes | Open-source music education is encouraged |
| Accept someone else's `.eic` and re-release it without credit | ✗ No | Always credit the original author |

### How to Give Proper Credit

When your project is based on someone else's work, use the `composer` field and comments:

```
project "My Arrangement of Moonlight Sonata"
composer "Ludwig van Beethoven (arr. Your Name)"

// Original composition by Ludwig van Beethoven
// This arrangement uses the public-domain score
// Modifications: added bass line, doubled tempo in section B

section "I. Adagio Sostenuto (After Beethoven)" {
    tempo 55
    include "parts/beethoven_melody.e" as melody
    include "parts/my_bass.e" as bass
    play melody with bass
}
```

### When Using MIDI Imports

Every MIDI file you import with `convert song.mid --project` creates an `index.ei` that you should edit to add proper attribution:

```
project "Imported Piece"
composer "Original Composer"     // ← CHANGE THIS to the real composer

// Source: name_of_song.mid — downloaded from [source]
// Converted to E on [date]
// I did not compose this. All credit to the original creator.
```

### Plagiarism Detection

E files can be signed (`sign` command) with the author's name and social links. If you find an unsigned `.eic` or `.e` file that matches a known composition without credit:

1. Check if it's signed (`info file.eic` shows the author if signed)
2. Compare against the original to see if meaningful changes were made
3. If it's clearly a copy without credit, call it out

### Educational Use

Importing songs to **learn** how they work is encouraged. Import Beethoven to see how he constructed a sonata. Import a pop song to study its chord progression. Just don't publish the result as your own work.

```
// Educational analysis of [Song Name]
// I imported this to study the chord progression
// Not for publication — personal learning only
```

### Sign Your Work

Always sign your original compositions so people know it's yours:

```powershell
E ...> sign my_song.eic
Author> Your Name
Instagram> @yourhandle
✓ Signed
```

---

## 52. Glossary

| Term | Meaning |
|------|---------|
| **BPM** | Beats Per Minute — how fast the music plays |
| **MIDI** | Musical Instrument Digital Interface — the standard protocol for digital music |
| **Note** | A single sound with a pitch (e.g., C4, A#3) |
| **Chord** | Multiple notes played at the same time |
| **Melody** | A sequence of single notes (the "tune") |
| **Harmony** | The chords that support the melody |
| **Rhythm** | The pattern of notes in time (long vs short) |
| **Dynamics** | How loud or soft the music is |
| **Velocity** | How hard a key is pressed (controls loudness) |
| **Octave** | 12 semitones — same note name, twice the frequency |
| **Semitone** | The smallest interval on a piano (one key to the next) |
| **Scale** | A set of notes that sound good together |
| **Key** | The "home" scale of a piece of music |
| **Tempo** | Speed of the music |
| **Timestamp** | When a note starts, measured in milliseconds from the beginning |
| **Duration** | How long a note lasts |
| **CC** | Control Change — MIDI messages for effects (reverb, chorus, pan) |
| **Quantization** | Snapping notes to a grid or scale |
| **Arpeggio** | Playing chord notes one after another instead of together |
| **Staccato** | Short, detached notes |
| **Legato** | Smooth, connected notes |
| **Crescendo** | Gradually getting louder |
| **Ritardando** | Gradually slowing down |
| **Accelerando** | Gradually speeding up |
| **FFT** | Fast Fourier Transform — algorithm that converts sound into frequencies |
| **EZip** | E's package format for mods and plugins |
| **GC** | Garbage Collection — automatic cleanup of messy note data |

---

## 53. MIT License

Copyright (c) 2024 Tentari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

> **Made by Tentari** — Instagram: @Tentari, Discord: @pixelhollow
> All `.eic` files display this copyright when compiled.

---

## 54. Architecture Overview

E is a **domain-specific language for piano music composition** that compiles to MIDI/WAV/MP3/MP4. Music is written as plain text and compiled into sound.

```
eshell.py              ← Interactive CLI shell (1051 lines)
ep_core.py             ← Core: plugin loader, signing, encryption, GC, variables
ep_pkg.py              ← Package manager: fetch, install, update, security scan
ep_compiler/ (21 files) ← Modular compiler: pipeline, events, formats, 6 syntax modes
    compile.py         ← Orchestrator — detect version, route to mode parser, compile events
    events.py          ← Event dicts: {timestamp, midi, duration, velocity, channel, ...}
    formats.py         ← Output: MIDI (mido), WAV (numpy+scipy), EC, EIC
    directives.py      ← @bpm, @key, @scale, @volume — parser
    import_midi.py     ← MIDI → events → .e source converter
    audio_transcribe.py ← Audio → MIDI via FFT (pydub + scipy)
    e_runtime.py       ← .ei project interpreter with DAG cycle detection
    mode_v1_machine.py ← T<N> N<N> D<N> V<N> token parser
    mode_v1_human.py   ← play note(C4) @dur:q parser
    mode_v3_extended.py ← v3 shorthand + macros + probability
    mode_v4_polyrhythm.py ← Polyrhythm, tuplets, Euclidean rhythms
    mode_v4_generative.py ← Generative algorithms
    mode_eci.py        ← Toggleable-mode .eci parser
    mode_enx.py        ← Album-index .enx parser
    scale_quantizer.py ← Snap notes to scale
player.py             ← Pygame MIDI player (console + glassmorphism GUI)
piano_synth.py        ← MIDI→WAV renderer via numpy/fluidsynth/ffmpeg
```

### Audio Pipeline

```
.e/.ei/.enx/.eci/.eic  →  Compiler (event list + BPM)  →  MIDI export (.mid)
                                                         →  Pygame player (console/GUI)
                                                         →  FluidSynth → WAV/MP3
                                                         →  Numpy synth → WAV/MP3
                                                         →  ffmpeg → MP3/MP4
```

Five configurable drivers (`audio set-driver <name>`):
- **numpy** (default) — clean harmonic synthesis, no external deps
- **fluidsynth** — SoundFont-based, needs `.sf2` file (auto-generated synthetic piano if missing)
- **microsoft** — Windows native MIDI synth via pygame.midi
- **ffmpeg** — direct MIDI→audio conversion

### Boot Sequence

1. `eshell.main()` starts
2. `restore_all()` — checks if any Tentari plugins are missing, restores from `embedded_plugins/*.json`
3. `core_init()` — loads encryption modules from `encryption/`, then loads plugins + mods
4. `show_boot_progress()` — animated progress bar showing each plugin/mod loading with status
5. `banner()` — prints E SHELL v2.1 header
6. Registers command dispatch dict
7. Starts hot-reload watcher thread
8. Enters interactive loop

---

## 55. Complete CLI Command Reference

Every command available in the E shell:

### cd `<dir>` — Change Directory

```
E ...> cd songs/
```

Uses `os.chdir()`. Defaults to project root if no arg. Errors print in red.

### ls `[dir]` — List Files

Color-coded by extension to quickly identify file types:
- `.e`, `.ei`, `.eic` → green (source files)
- `.mid`, `.wav`, `.mp3`, `.mp4` → yellow (audio output)
- `.ee`, `.ec`, `.ecc` → red (encrypted)
- `.py` → magenta (Python scripts)
- Directories → cyan
- Everything else → grey

Shows file size in KB or B.

### compile `<file> [-o <out>] [--human] [--machine] [--volume N]`

The core compilation command. Accepts: `.e`, `.ei`, `.eci`, `.enx`, `.eic`.

**Pipeline:** detect syntax → route to parser → event list → sort → GC → export

**Output formats:** `.mid` (default), `.wav`, `.mp3`, `.mp4`, `.ec`, `.eic`, `.ee`, `.ecc`

**Flags:**
- `--human` — Recompile `.eic` to human-readable `.e` source
- `--machine` — Recompile `.eic` to machine-format `.e` source
- `--volume 0.8` — Master volume override applied to output

### play `<file> [--gui]` — Play

Plays through one of two players:

**ConsolePlayer** (default): pygame.midi output, keyboard controls (`+`/`-` volume, `←`/`→` seek ±5s, `Space` pause, `ESC` quit). Volume persisted to `.player_volume.json`.

Takes `.e/.ei/.enx/.eci/.eic` through compile→MIDI→play pipeline. Also plays `.mid/.wav/.mp3/.mp4` directly.

**EPlayer** (GUI with `--gui`): Glassmorphism-themed pygame window with waveform visualization, time elapsed/total, volume bar, same keyboard controls.

### info `<file>` — Show File Metadata

Parses compiled events and displays:
- Event count, duration in seconds, BPM
- Average velocity, most common notes
- MIDI channels used
- If signed: author name + social links + truncated signature hash

### convert `<input> -o <output> [--project]` — Import

Imports external formats into E:

**MIDI import** (.mid, .midi): Parses track-by-track via `mido`. Extracts note-on/off, tempo, time sig. `--project` generates full `.ei` project with `parts/` directory.

**Audio transcription** (.wav, .mp3, .mp4, .flac, .ogg, .aac, .m4a): FFT-based pitch detection via pydub + scipy. Detects onsets, quantizes to semitones. Outputs `.e` file. Requires `pip install pydub scipy`.

### sign `<file> [--embed]` — Sign Files

HMAC-SHA256 signing system. Full details in section 56.

### encrypt `<file> [-o <out.ee>]` — Encrypt Source

XOR/AES-GCM encryption. Full details in section 57.

### ecc `<file> [-o <out.ecc>]` — Compile + Encrypt

One-step compile-and-encrypt. Compiles → events → encrypts → `.ecc`.

### mod `<cmd>` — Mod Management

Security-sandboxed extensions. Mods run with restricted builtins (no file I/O, no import, no subprocess, no network). AST-scanned before loading.

| Subcommand | Effect |
|------------|--------|
| `mod list` | List installed mods from `mods/` |
| `mod list-avail` | List available mods from pkglist |
| `mod install <name>` | Install from pkglist |
| `mod remove <name>` | Uninstall |
| `mod scan` | AST security scan all installed mods |
| `mod sign <name>` | Sign with author metadata |
| `mod disable <name>` | Skip on next boot |
| `mod enable <name>` | Re-enable |
| `mod version` | Check installed vs available versions |

### plugin `<cmd>` — Plugin Management

Same subcommands as `mod` but for full-access plugins (no sandbox).

| Subcommand | Effect |
|------------|--------|
| `plugin list` | List installed plugins from `plugins/` |
| `plugin list-avail` | List available from pkglist |
| `plugin install <name>` | Install from pkglist (file:// or embedded JSON backup) |
| `plugin remove <name>` | Uninstall (permanent — no auto-restore on hot-reload) |
| `plugin scan` | Security scan all installed plugins |
| `plugin sign <name>` | Sign with author metadata |
| `plugin disable <name>` | Skip on next boot |
| `plugin enable <name>` | Re-enable |
| `plugin version` | Check installed vs available versions |

### pkglist `<cmd>` — Package Registry

| Subcommand | Effect |
|------------|--------|
| `pkglist show` | Show summary: mod count, plugin count, last updated, sync URL |
| `pkglist detail` | Full detail on every available package |
| `pkglist install <name>` | Install from pkglist |
| `pkglist search <query>` | Search packages by name/description/tags |
| `pkglist update file <path>` | Load pkglist from local JSON file |
| `pkglist update url <url>` | Fetch pkglist from HTTP URL |
| `pkglist version` | Version check: installed vs available for all packages |

### ezip `install|list <file>` — EZip Packages

Installs `.ezip` bundles (zip with `EzPk` magic + `manifest.json`). Security-scanned before extraction.

### gc `<cmd>` — Garbage Collection

Cleans messy event data:

| Subcommand | Effect |
|------------|--------|
| `gc enable` | Enable GC on compile |
| `gc disable` | Disable GC |
| `gc status` | Show state + strategy + event count |
| `gc flush` | Run default GC on last compiled events |
| `gc clean` | Run aggressive GC (merges overlaps by pitch + channel) |
| `gc default` | Set strategy to default |
| `gc aggressive` | Set strategy to aggressive |

**Default GC**: Removes out-of-range MIDI (0-127), clamps velocity, removes zero-duration events, deduplicates identical events at same timestamp.

**Aggressive GC**: Everything default does + merges overlapping same-pitch same-channel notes unless velocity differs by >12 or overlap is small relative to duration or gap between note-ons is large.

### sys `<cmd>` — System Management

| Subcommand | Effect |
|------------|--------|
| `sys status` | Show version, plugin/mod count, GC state, last compiled events |
| `sys scan` | Security scan all mods |
| `sys reload` | Force-reload all plugins + mods from disk (clears caches, re-init core) |
| `sys reset` | Factory reset: clear plugins, mods, caches, disabled state |
| `sys panic` | Emergency stop: disables ALL plugins, clears caches, disables GC |

### audio `<cmd>` — Audio Configuration

| Subcommand | Effect |
|------------|--------|
| `audio devices` | List MIDI input/output devices |
| `audio set-device <id>` | Set active MIDI output device |
| `audio set-driver <name>` | Set render driver: `numpy`, `fluidsynth`, `microsoft`, `ffmpeg` |
| `audio set-sr <hz>` | Set sample rate (44100/48000/96000) |
| `audio set-bit <depth>` | Set bit depth (16/24/32) |
| `audio set-ch <n>` | Set channels (1 mono/2 stereo) |
| `audio config` | Show current audio config |

Persisted to `.synth_config.json`.

### clear — Clear Screen
Clears the terminal and re-draws the banner.

### exit — Quit
Exits the E shell.

---

## 56. Signing System

HMAC-SHA256 based. Every file can carry a signature block proving authorship.

### How to Sign

```
E ...> sign my_song.e
Author> Tentari
Instagram> @tentari
Discord> @pixelhollow
✓ Signed
```

The signature is computed over the file content using the key `"e-lang-signature-key"`. Any modification to the file breaks the signature.

### Sidecar Mode (default)

Creates `<file>.sig` containing the signature metadata:

```json
{
    "algorithm": "HMAC-SHA256",
    "signature": "a1b2c3d4e5f6...",
    "timestamp": 1734567890.0,
    "file": "my_song.e",
    "author": "Tentari",
    "social": {
        "Instagram": "@tentari",
        "Discord": "@pixelhollow"
    }
}
```

### Embedded Mode (`--embed`)

Injects signature JSON into the first line of the file. Used for `.ec`, `.eic`, `.ee` formats:

```
{"_e_sig": {"signature": "a1b2...", "author": "Tentari", ...}}
<original file content>
```

### Verification

```
E ...> info signed_file.e
```

Checks for sidecar `.sig` file or embedded `_e_sig` JSON. Verifies HMAC-SHA256. Prints author + social links with colored display.

---

## 57. Encryption System

Two built-in encryptors + custom encryption module support.

### Encrypt a File

```
E ...> encrypt my_song.e -o my_song.ee
```

Writes `.ee` with a JSON header + encrypted payload:

```
{"method": "aes_gcm", "key_hint": "a1b2c3d4"}
<encrypted binary data>
```

### Available Encryptors

**Base encryptor** (default, built into core):
- XOR cipher with SHA-256 stretched key + base64
- `encrypted = base64(xor(data, key))`
- Key default: `"e-lang-default"`
- Simple, fast, no dependencies

**AES-256-GCM** (`encryption/aes_gcm.py`):
- Uses `Crypto.Cipher.AES` from PyCryptodome if available
- Falls back to XOR if PyCryptodome not installed
- scrypt key derivation (N=16384, r=8, p=1)
- 128-bit random nonce per file

**Custom XOR** (`encryption/custom_xor.py`):
- Double XOR with SHA-256 expanded key
- Registered as `"custom_xor"` encryptor

### Bundle Encryption (`ecc`)

Compiles first, then encrypts the compiled event data:

1. `compile_source(file)` → events + bpm
2. `json.dumps(events)` → bytes
3. Encrypt with selected method
4. Write `.ecc` with header + encrypted payload

Decryption happens entirely in-memory — no plaintext written to disk.

---

## 58. Complete File Extension Reference

### Core Source Formats

#### `.e` — E Source File (v1+)

The universal source format. Contains E language code in any syntax version. Compiler auto-detects which parser to use.

#### `.ei` — E Project Index (v1+)

Multi-file composition index. References external parts via `include`:

```
project "Moonlight Sonata"
composer "Beethoven"

section "I. Adagio" {
    include "parts/melody.e" as melody
    include "parts/bass.e" as bass
    play melody with bass
}
```

Supports:
- `include "path"` / `include "path" as alias`
- `section "name" { ... }` with local tempo/instrument overrides
- `play X with Y` — layer multiple parts simultaneously
- `tempo N` / `instrument NAME` — section-local overrides
- DAG cycle detection prevents circular includes

#### `.enx` — Album Root Index (v3+)

Links multiple `.ei` projects into a single collection:

```
album "My Piano Works"
artist "Tentari"
year 2024
track 1 "Nocturne" include "nocturne/index.ei"
track 2 "Waltz" include "waltz/index.ei"
```

#### `.eci` — Toggleable Mode File (v3+)

Switches between multiple syntax modes mid-document:

```
#MACHINE
T0 N60 D500
#HUMAN
play note(C4) @dur:q
#V3
C4 q
```

Supported mode directives: `#MACHINE`, `#HUMAN`, `#V3`/`#SHORTHAND`, `#V4`

### Compiled / Distribution Formats

#### `.mid` — Standard MIDI File (v1+)

Type 1 multi-track MIDI via `mido`. Contains note events, tempo meta-events, time sig, track names, controller events. All syntax versions compile down to `.mid`.

#### `.eic` — Compiled Events with Source (v2+)

Contains compiled event list PLUS the original `.e` source embedded. Enables round-trip:

```
@bpm 120
{"t":0,"n":60,"d":500,"v":100}
--- E SOURCE ---
@bpm 120
play note(C4) @dur:q @vel:mf
```

Allows `play` (instant from compiled events) AND `compile --human` (extract to readable source).

#### `.ec` — Compiled Events Only (v2+)

Just the event list without source. Smaller, faster load, no round-trip.

### Encrypted Formats

#### `.ee` — Encrypted E Source (v2+)

Source encrypted with cipher. Play/compile decrypts in-memory. No plaintext written to disk.

#### `.ecc` — Compiled + Encrypted (v2+)

One-step compile-and-encrypt. Decrypts, parses events, feeds to MIDI output.

### Security Formats

#### `.sig` — Sidecar Signature (v3+)

HMAC-SHA256 signature stored alongside the signed file.

### Package Formats

#### `.ezip` — E Zip Package (v3+)

Distribution format for mods/plugins. Zip with `EzPk` magic + `manifest.json` + Python source files.

### Backup / Runtime Formats

| File | Version | Purpose |
|------|---------|---------|
| `embedded_plugins/<name>.json` | v3+ | Base64 plugin backup with SHA-256 hashes |
| `.synth_config.json` | v3+ | Audio driver persistence |
| `.player_volume.json` | v3+ | Player volume persistence |
| `.fent_cache/` | v3+ | Compilation cache directory |

### Extension Table by Version

| Extension | v1 | v2 | v3 | v4 | Purpose |
|-----------|----|----|----|----|---------|
| `.e` | ✅ | ✅ | ✅ | ✅ | Universal source |
| `.ei` | ✅ | ✅ | ✅ | ✅ | Multi-file project |
| `.mid` | ✅ | ✅ | ✅ | ✅ | Standard MIDI output |
| `.ec` | ❌ | ✅ | ✅ | ✅ | Compiled events only |
| `.eic` | ❌ | ✅ | ✅ | ✅ | Compiled events + source |
| `.ee` | ❌ | ✅ | ✅ | ✅ | Encrypted source |
| `.ecc` | ❌ | ✅ | ✅ | ✅ | Compiled + encrypted |
| `.enx` | ❌ | ❌ | ✅ | ✅ | Album/index root |
| `.eci` | ❌ | ❌ | ✅ | ✅ | Toggleable modes |
| `.sig` | ❌ | ❌ | ✅ | ✅ | Sidecar signature |
| `.ezip` | ❌ | ❌ | ✅ | ✅ | Package bundle |

### Pipeline by Extension

```
SOURCE                → ACTION              → OUTPUT
.e (any version)      → compile             → .mid/.wav/.mp3/.mp4
.ei (project)         → resolve includes    → .mid/.wav
.enx (album)          → compile all refs    → .mid/.wav
.eci (toggle modes)   → track mode per line → .mid/.wav
.e                    → compile + encrypt   → .ecc
.e                    → encrypt             → .ee
.ee                   → decrypt → compile   → .mid/.wav
.ecc                  → decrypt → play      → audio
.eic                  → play (instant)      → audio
.eic --human          → extract → human     → .e
.eic --machine        → extract → machine   → .e
```

---

## 59. Package Manager

Two-tier system: **mods** (sandboxed, security-scanned) and **plugins** (full access).

### Mods vs Plugins

| | Mods | Plugins |
|--|------|---------|
| Location | `mods/` | `plugins/` |
| Entry | `init(api)` | `register(api)` |
| Security | AST-scanned + restricted builtins | Full Python access |
| Use case | Simple extensions | Full-featured packages |

### Security Model

- **Mod loading**: AST-based analysis blocks `os.system`, `eval`, `exec`, `subprocess`, `socket.connect`, etc. Runs with restricted builtins (no file I/O, no import).
- **Plugin loading**: No sandbox — full access. User explicitly installs plugins.
- **Package install**: Every downloaded file is AST-scanned before saving.
- **Self-disabling**: `_fatal()` auto-disables any plugin/mod that crashes during load.

### Fetch/Install Flow

1. Look up package in `pkglist.json`
2. Try `file://` URL → copy from local filesystem
3. If `file://` fails → try `embedded_plugins/<name>.json` (Tentari backup — no network needed)
4. If embedded fails → HTTP download from registry
5. AST security scan → extract → `_auto_reload()`

### Embedded Backup

All Tentari-signed plugins stored as base64 JSON in `embedded_plugins/`:
- `fentclient.json` (12 files, 71 KB)
- `lure.json` (7 files, 20 KB)
- `portbaby.json` (18 files, 25 KB)

`plugin install <name>` auto-falls back to these if the `file://` path is missing. No network required for Tentari plugins.

---

## 60. Plugins by Tentari

### Fentclient v1.0.0 (12 modules)

Performance accelerator, bug fixes, and enhanced syntax for E. Every module is a full implementation:

| Module | What it does |
|--------|-------------|
| `fixer.py` | Runtime patches: Ctrl+C isolation, MIDI volume fallback, arrow key seek, dead code removal from player |
| `directives.py` | Registers `@fent:*` syntax directives for volume, EQ, reverb, delay, DSP presets, culling, soundfont, arpeggiator, chord, pattern, theory, AI, pitch, quality, freq |
| `commands.py` | CLI handlers for all `fent *` subcommands (status, inspect, record, watch, theory, ai, batch, fx, cache, doctor) |
| `engine.py` | FluidSynth engine wrapper. Auto-generates a playable SoundFont if none exists (`_generate_sf2` produces a valid SF2 with harmonic piano waveform + ADSR envelope). Renders MIDI→WAV via subprocess |
| `arpeggiator.py` | 8 arpeggio modes: up, down, updown, random, chord, bass, walkup, pedal. Configurable rate, octave range, step count. Chord-event expansion |
| `theory.py` | 18 chord formulas, 10 progression styles (pop, rock, blues, jazz, classical, doo-wop, epic, minor, andalucian, mixolydian). Key detection from MIDI notes. Composition checking with chromatic detection. Harmonization via parallel thirds |
| `dsp.py` | Reverb (ring buffer with configurable decay), delay (feedback line with mix), biquad peaking EQ, compressor with knee. Full WAV file processing pipeline |
| `cache.py` | SHA-256 file hash + mtime compilation cache. Persisted to `.fent_cache/`. Text-content cache for raw source. Clear and stats commands |
| `culler.py` | Event culling: remove sub-threshold velocity notes, reduce polyphony (keeps loudest N simultaneous notes). FFmpeg filter graph generation. Temp-file export for MIDI pipeline |
| `recorder.py` | `MIDIRecorder` class — threaded pygame.midi input capture. Note-on/off tracking with duration calculation. Device enumeration and selection. `.e` export with timestamp quantization |
| `watcher.py` | Background file watcher — 1-second mtime polling. Auto-recompile + auto-play on save. Resilient error handling (stops after 5 consecutive errors or 20 total). 300ms debounce between change detection and action |

### LURE v3.0.0 — Lua Runtime Accelerator

Accelerates compilation using LuaJIT via `lupa`. Python manages state; Lua handles fast string parsing and bulk event math.

- **3-10x speedup** on batch parsing (10,000+ lines)
- **GIL-free**: lupa releases GIL during Lua execution
- **Graceful fallback**: if `lupa` not installed, reports inactive
- **5 Lua modules**: compiler.lua (line parser), events.lua (validation/dedup), quantizer.lua (scale snap), midi_export.lua (tick math), directives.lua (@bpm/@key/@scale)
- **Commands**: `lure status`, `lure benchmark`

### Portbaby v1.0.0 — Syntax Version Porting

Converts projects between ALL syntax versions with loss percentage reporting.

- **18 converter modules** — v1↔v2↔v3↔v4 in every direction + v1_human↔v1_machine
- **Loss calculator**: tracks what's lost per version downgrade
- **Project builder**: generates multi-file `.ei` project structure
- **Detectors**: auto-detect source syntax version
- **Commands**: `portbaby <file> --to <version> [--project] [--report]`, `pb` alias
- **Targets**: v1_machine, v1_human, v2, v3, v4, v4_human

---

## 61. Hot-Reload Watcher

Background daemon thread polls files every 1 second after boot:

1. Takes mtime snapshot of all `.py`, `.lua`, `.json`, `.e`, `.ei`, `.enx` files across `plugins/`, `mods/`, `ep_compiler/`, `tools/` + root `.py`/`.lua` files
2. On change: clears all plugin/mod/compiler/encryption caches, force-reloads `ep_core` from disk (not cached), re-initializes with animated boot progress bar, re-registers commands
3. Shows diff: `+new_file.py` (added), `~modified.py` (changed), `-deleted.py` (removed)
4. 3-second debounce after any reload to prevent cascading triggers
5. Skips if `_auto_reload()` was called within 3 seconds (prevents double-fire from `plugin install`)

The watcher monitors approximately 100 files across the entire project tree.

---

## 62. Security Model

| Component | Protection |
|-----------|-----------|
| Mod loading | AST-based analysis blocks dangerous patterns. Runs with restricted builtins |
| Plugin loading | No sandbox — full access (user trusts what they install) |
| Package install | Every downloaded/scanned file is AST-checked before saving |
| File signing | HMAC-SHA256 with author metadata. Sidecar or embedded modes |
| Encryption | XOR or AES-256-GCM with scrypt key derivation |
| Self-disabling | `_fatal()` auto-disables any plugin/mod that crashes during load |
