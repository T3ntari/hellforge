# **HELLFORGE v1.0.0.0 ALPHA — portbaby: Syntax Version Porting**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**portbaby** translates Piano DSL source code between syntax versions v1, v2, v3, and v4. It enables projects written in older syntax to run on newer engines and vice versa.

## Version Mapping

| v1 (Legacy)       | v2 (Stable)          | v3 (Modern)          | v4 (Current)         |
|-------------------|----------------------|----------------------|----------------------|
| `kernel foo() =`  | `@kernel fn foo()`   | `@compute fn foo()`  | `kernel foo()`       |
| `matrix a,b`      | `tensor a,b`         | `Tensor a,b`         | `mat a,b`            |
| `shader{...}`     | `@vertex{...}`       | `fn vs(){...}`       | `vsh{...}`           |
| `audio@buf`       | `@audio buffer`      | `let buf:AudioBuf`   | `abuf buf`           |

## Porting Rules

portbaby matches source files against syntax version signatures and applies transformation passes:

1. **Lexer tricking** — pre-tokenizes the source to detect version
2. **AST rewriting** — transforms nodes between version schemas
3. **Semantic validation** — ensures ported output is valid for the target version
4. **Fallback annotation** — inserts `@compat` annotations where lossy conversion occurs

## Backport / Forward Port

- `@target v1` — produces v1-compatible output (lossy)
- `@target v2` — safe round-trip for most constructs
- `@target v3` — full feature mapping
- `@target v4` — preserves all features, may expand syntactic sugar

---

**API Reference:** `#include <portbaby/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — portbaby: Syntax Version Porting**
