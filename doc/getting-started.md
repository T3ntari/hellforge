**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [getting-started](getting-started.md) | [contributing](contributing.md) | [changelog](changelog.md) | [faq](faq.md)

## Getting Started

### Installation

Download the latest HELLFORGE release for your platform:

- Windows: `piano-installer-x64.exe`
- macOS: `piano-darwin-arm64.tar.gz`
- Linux: `piano-linux-x64.tar.gz`

### First Compile

Create `hello.piano`:

```piano
print("Hello, Piano DSL!")
```

Compile and run:

```
piano run hello.piano
```

### Hello World with Audio

```piano
eaudio.open()
let tone = eaudio.synth.sine(440.0, duration = 2.0)
eaudio.play(tone)
```

### Next Steps

- Explore the signing system to secure your plugins
- Try GPU compute with Radical and TensorSHARP
- Build a game engine with OPENapi and Vulkanizer

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**