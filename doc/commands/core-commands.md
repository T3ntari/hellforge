# HELLFORGE v1.0.0.0 ALPHA — Core Commands

> Navigation: [doc/index.md](../index.md)

## cd
**Syntax:** `cd <path>`
**Description:** Change the current working directory within the eshell environment.
**Example:** `cd examples/`
**Plugin:** built-in (core eshell)

## ls
**Syntax:** `ls [path]`
**Description:** List files and directories in the specified path or current directory.
**Example:** `ls doc/commands/`
**Plugin:** built-in (core eshell)

## compile
**Syntax:** `compile <file.e> [-o output]`
**Description:** Compile a piano-dsl `.e` composition file into a playable audio format.
**Example:** `compile lullaby.e -o lullaby.wav`
**Plugin:** built-in (core eshell)

## play
**Syntax:** `play <file.e>`
**Description:** Compile and immediately play a composition through the default audio output.
**Example:** `play techno_beat.e`
**Plugin:** built-in (core eshell)

## gui
**Syntax:** `gui [--theme <name>]`
**Description:** Launch the piano-dsl graphical composition editor interface.
**Example:** `gui --theme dark`
**Plugin:** built-in (core eshell)

## info
**Syntax:** `info [--all]`
**Description:** Display system information, loaded plugins, and environment status.
**Example:** `info --all`
**Plugin:** built-in (core eshell)

## convert
**Syntax:** `convert <input> -f <format> [-o output]`
**Description:** Convert between supported audio and composition formats.
**Example:** `convert lullaby.wav -f mp3 -o lullaby.mp3`
**Plugin:** built-in (core eshell)

## encrypt
**Syntax:** `encrypt <file> [-k keyfile]`
**Description:** Encrypt a composition file using built-in cipher.
**Example:** `encrypt lullaby.e -k mykey.pub`
**Plugin:** built-in (core eshell)

## ecc
**Syntax:** `ecc <mode> [options]`
**Description:** Elliptic-curve cryptography utilities for key generation and signing.
**Example:** `ecc genkey -o composer.key`
**Plugin:** built-in (core eshell)

## mod
**Syntax:** `mod <name>`
**Description:** Load or unload a piano-dsl plugin module by name.
**Example:** `mod load radical`
**Plugin:** built-in (core eshell)

## plugin
**Syntax:** `plugin list|info|install|remove <name>`
**Description:** Manage installed plugins — list, inspect, install from registry, or remove.
**Example:** `plugin list`
**Plugin:** built-in (core eshell)

## audio
**Syntax:** `audio list|select|test <device>`
**Description:** List, select, or test audio output devices.
**Example:** `audio list`
**Plugin:** built-in (core eshell)

## ezip
**Syntax:** `ezip <file> [-o archive.ezp]`
**Description:** Package composition files and assets into a compressed archive.
**Example:** `ezip lullaby.e -o lullaby.ezp`
**Plugin:** built-in (core eshell)

## gc
**Syntax:** `gc [--force]`
**Description:** Run garbage collection to free unused memory in the eshell runtime.
**Example:** `gc --force`
**Plugin:** built-in (core eshell)

## sys
**Syntax:** `sys info|stats|log [options]`
**Description:** Display system diagnostics, resource usage statistics, or runtime logs.
**Example:** `sys stats`
**Plugin:** built-in (core eshell)

## pkglist
**Syntax:** `pkglist [--installed] [--available]`
**Description:** List all installed or available packages and their versions.
**Example:** `pkglist --installed`
**Plugin:** built-in (core eshell)

## clear
**Syntax:** `clear`
**Description:** Clear the eshell terminal screen.
**Example:** `clear`
**Plugin:** built-in (core eshell)

## help
**Syntax:** `help [command]`
**Description:** Display help information for a specific command or list all commands.
**Example:** `help compile`
**Plugin:** built-in (core eshell)

## exit
**Syntax:** `exit`
**Description:** Exit the eshell environment gracefully.
**Example:** `exit`
**Plugin:** built-in (core eshell)

## quit
**Syntax:** `quit`
**Description:** Alias for exit — terminate the eshell session.
**Example:** `quit`
**Plugin:** built-in (core eshell)

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
