# Launcher — Window Launching & Process Management

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [launcher](launcher.md) | [learner](learner.md)

---

## Overview

**LAUNCHER v1.0.0** (author Tentari) opens players, compilers, files and
shells in dedicated windows and manages running HELLFORGE processes. Logs
land in `logs/` via `_launch.py`.

## Commands

```
launcher open <file>           open a file with the default application
launcher player <file> [--gui] launch the player in a new window
launcher compile <file> -o <out> [--human|--machine]   compile in a new window
launcher shell [--project <dir>]  open an eshell in a new window
launcher log <name>            show a launcher log
launcher ps                    list running HELLFORGE processes
launcher kill <pid>            kill a process
```

Alias: `launch` (`(alias)` in help).
