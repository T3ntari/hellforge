**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [custom-plugin](examples/custom-plugin.md) | [gpu-compute](examples/gpu-compute.md) | [game-engine](examples/game-engine.md)

## Custom Plugin Creation

This guide walks through creating a Piano DSL plugin from scratch.

### Step 1: Scaffold

```
piano plugin new my-audio-tool
```

Creates the following structure:

```
my-audio-tool/
  plugin.json
  src/
    main.piano
  assets/
```

### Step 2: Write the Plugin

Edit `src/main.piano`:

```piano
plugin "my-audio-tool" version "1.0.0"

export function process(input: float32[]) -> float32[] {
    return input.map(sample => sample * 0.5)
}
```

### Step 3: Build

```
piano plugin build my-audio-tool
```

### Step 4: Sign

```
piano sign --plugin my-audio-tool.pkg
```

### Step 5: Install Locally

```
piano pkg install ./my-audio-tool.pkg
```

### Step 6: Publish

Upload the `.pkg` and `.sig` to your distribution channel.

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**