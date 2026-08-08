# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## Shell Commands — Full eshell Reference

Piano DSL embeds an eshell for interactive control during playback.

### Playback Control

| Command | Description |
|---------|-------------|
| `play` | Start playback from current position |
| `play from <section>` | Play from a named section |
| `play loop` | Play on infinite repeat |
| `stop` | Stop playback |
| `pause` | Pause at current position |
| `resume` | Resume from pause |
| `seek <tick>` | Jump to tick position |
| `rewind` | Seek to tick 0 |

### State Queries

| Command | Description |
|---------|-------------|
| `status` | Show current BPM, key, volume, tick |
| `vars` | List all defined variables with values |
| `sections` | List all named sections |
| `scope` | Show current scope stack |

### Rendering & Export

| Command | Description |
|---------|-------------|
| `render` | Render to internal buffer |
| `export midi <file>` | Export as Standard MIDI File |
| `export wav <file>` | Export as WAV audio |
| `export json <file>` | Export as structured JSON |
| `export score <file>` | Export as PDF score |

### Configuration

| Command | Description |
|---------|-------------|
| `set bpm <n>` | Change BPM at runtime |
| `set key <name>` | Change key signature |
| `set vol <n>` | Set global volume |
| `set ch <n>` | Set MIDI channel |
| `reset` | Reset all state |

### Debug

| Command | Description |
|---------|-------------|
| `debug on` | Enable verbose logging |
| `debug off` | Disable verbose logging |
| `ast` | Print current AST for loaded file |
| `trace <line>` | Trace evaluation of a specific line |
| `profile` | Show performance profile |

### Examples

```
> play from Chorus
> set bpm 160
> vars
  $bpm = 160
  $vel = 100
  $octave = 4
> export midi "output/chorus.mid"
  Exported 1248 events.
```

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
