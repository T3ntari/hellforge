# E Language — Complete System Guide

## Overview

E is a domain-specific language for piano music composition. The system includes:
- **ep.py** — Compiler/player CLI (`.e` → `.mid`, `.wav`, `.mp3`, `.mp4`, `.ec`)
- **ai.py** — AI agent with Plan/Build modes (Ollama local + Cloud API)
- **tools/** — MIDI ↔ E converters (midi2e.py, e2midi.py)

## Quick Start

```powershell
cd E:\piano-dsl
python ep.py compile input.e -o output.mid   # Compile to MIDI
python ep.py play input.e                     # Stream to synth
python ai.py                                  # AI composer shell
```

## File Types

| Extension | Purpose |
|-----------|---------|
| `.e` | E source file |
| `.ei` | Project index (multi-file manifest) |
| `.ec` | Compiled binary (instant load) |
| `.mid` | Standard MIDI output |

## E Language Syntax

### #MACHINE Mode (AI-friendly, stateless)
```
@bpm 140
T0 N36 D500 V0.7
T0 N60 D250 V0.8
T428 N64 D250 V0.9
```

Format: `T<ms> N<midi> D<ms> V<0.0-1.0>`
- `T` = absolute time in milliseconds
- `N` = MIDI note (60=C4, 72=C5, 36=C2)
- `D` = duration in ms
- `V` = velocity 0.0-1.0

### #HUMAN Mode (readable)
```
play note(C4) @dur:q @vel:mf
play chord(C, major) @dur:h @vel:ff @strum:down(15ms)
```

## MIDI Note Reference
```
C4=60  D4=62  E4=64  F4=65  G4=67  A4=69  B4=71  C5=72
C3=48  C2=36  C1=24  C0=12
Add 12 per octave up, subtract 12 down.
```

## CLI Tools

### ep.py — Compiler & Player
```powershell
python ep.py compile input.e -o output.mid     MIDI
python ep.py compile input.e -o output.wav     WAV audio
python ep.py compile input.e -o output.mp3     MP3 (requires ffmpeg)
python ep.py compile input.e -o output.mp4     Video + audio (ffmpeg)
python ep.py compile input.e -o output.ec      Compiled binary
python ep.py compile input.e -o output.human   Convert to #HUMAN
python ep.py compile project.ei -o output.wav  Multi-file project
python ep.py play input.e                      Stream to synth
python ep.py info input.e                      Stats
```

### tools/midi2e.py — MIDI → E
```powershell
pip install music21
python tools/midi2e.py song.mid -o song.e
python tools/midi2e.py *.mid --outdir ./e_files
```

### tools/e2midi.py — E → MIDI
```powershell
pip install mido
python tools/e2midi.py song.e -o song.mid
```

## ai.py — AI Agent

Start:
```powershell
python ai.py
```

Select model from cloud API or local Ollama. Then use commands:

### Commands
```
project <name>     Create project
write <path>       Write file (paste content, end with ---)
edit <path>        Find/replace
delete <path>      Delete file (asks ALL/1/N)
read <path>        Show file (read <path> 10-20 for line range)
ls                 List files
compile            Compile to MIDI
play               Play via synth
/plan <desc>       AI designs a composition plan
/build <desc>      AI generates code from plan
/quit              Exit
```

### Cloud API
Base URL: `https://opencode.ai/zen/go/v1`
Models available: deepseek-v4-flash, qwen3.7-plus, kimi-k3, glm-5, etc.

Set key:
```powershell
set E_OPENAI_KEY=sk-your-key
set E_OPENAI_URL=https://opencode.ai/zen/go/v1
```

## Project Structure
```
piano-dsl/
├── ep.py                 Compiler & player
├── ai.py                 AI agent entry point
├── ai/                   AI agent package
│   ├── agent.py          Agent loop
│   ├── cli.py            CLI entry
│   ├── config.py         Paths, colors
│   ├── ollama.py         API clients (Ollama + OpenAI)
│   ├── prompts.py        System prompts
│   ├── session.py        Session save/load
│   └── tools.py          File operations
├── tools/
│   ├── midi2e.py         MIDI converter
│   ├── e2midi.py         E to MIDI
│   └── dl_fluidsynth.py  SoundFont setup
├── examples/             Example .e files
├── ai_generated/         AI output directory
└── projects/             Multi-file projects
```

## Environment Variables
```
E_OPENAI_KEY     API key for cloud models
E_OPENAI_URL     Base URL (default: https://opencode.ai/zen/go/v1)
```
