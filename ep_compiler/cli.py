"""CLI entry point for the E Language Compiler v4."""
import argparse
import os
import sys
import json
import tempfile

from .compile import (
    compile_source,
    compile_file as compile_auto,
    detect_syntax_version,
)
from .events import (
    validate_events,
    sort_events,
    midi_to_name,
)
from .formats import (
    export_midi,
    export_ec,
    export_wav,
    export_eic,
)
from .directives import (
    parse_directives,
    parse_config_strip,
)
from .mode_v4_polyrhythm import process_polyrhythms
from .mode_v4_generative import process_generative


def compile_file(path, output=None, fmt="midi", volume=None, effects=None, bpm_override=None, strict=False):
    """Compile any E format (.e/.ei/.eic/.eci/.enx) to output format."""
    ext = os.path.splitext(path)[1].lower()
    project_formats = {".ei", ".enx", ".eci", ".eic"}

    if ext in project_formats or ext == ".e":
        events, bpm = compile_auto(path, bpm_override, strict=strict)
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        text = process_polyrhythms(text)
        text = process_generative(text)
        events, bpm = compile_source(text, bpm_override, strict=strict)

    if bpm_override:
        bpm = bpm_override

    if volume is not None:
        for e in events:
            e["master_vol"] = volume

    events, _ = validate_events(events)
    events = sort_events(events)

    # Low-level render params from @sr/@bit/@quality/@gain/@sub/@bass_boost/
    # @stereo_width/@neural directives in the source
    render_params = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            _src = f.read()
        from .directives import parse_directives
        _ll = parse_directives(_src)
        for _k, _v in (("sr", "sample_rate"), ("bit", "bit_depth"),
                       ("quality", "quality"), ("sub", "sub"),
                       ("bass_boost", "bass_boost"), ("stereo_width", "stereo_width"),
                       ("neural", "neural")):
            if _ll.get(_k) is not None:
                render_params[_v] = _ll[_k]
        if _ll.get("master_vol") is not None:
            render_params["gain"] = float(_ll["master_vol"])
    except Exception:
        pass

    if output is None:
        base = os.path.splitext(path)[0]
        ext_map = {"midi": ".mid", "mid": ".mid", "ec": ".ec", "wav": ".wav",
                   "eic": ".eic", "mp3": ".mp3"}
        output = f"{base}{ext_map.get(fmt, '.' + fmt.lstrip('.'))}"

    out_ext = os.path.splitext(output)[1].lower()
    if out_ext in (".mid", ".midi"):
        export_midi(events, bpm, output)
    elif out_ext == ".ec":
        export_ec(events, bpm, output)
    elif out_ext == ".wav":
        export_wav(events, bpm, output, params=render_params)
    elif out_ext == ".eic":
        # Generate .eic from .ei or .e source
        export_eic(path, output)
        return True
    else:
        # Unknown format — never recurse into ep.py (infinite spawn bug).
        print(f"  ! Unsupported output format: {out_ext} (supported: .mid, .ec, .wav, .eic)")
        return True

    if os.path.exists(output):
        sz = os.path.getsize(output) // 1024
        print(f"  > {output} ({sz}KB)")
    return True


def import_file(input_path, output=None, project=False):
    """Import MIDI/audio to .e source or full project."""
    ext = os.path.splitext(input_path)[1].lower()
    audio_exts = {".wav", ".mp3", ".mp4", ".m4a", ".mov", ".avi", ".flac", ".ogg", ".aac", ".wma", ".aiff"}

    if ext in (".mid", ".midi"):
        from .import_midi import (
            import_midi,
            events_to_e_source,
            midi_to_e_project,
        )
        if project:
            out_dir = output or os.path.splitext(os.path.basename(input_path))[0] + "_project"
            midi_to_e_project(input_path, out_dir)
            return True
        events, bpm = import_midi(input_path)
    elif ext == ".ec":
        from .import_midi import (
            import_ec,
            events_to_e_source,
        )
        events, bpm = import_ec(input_path)
    elif ext in audio_exts:
        from .audio_transcribe import transcribe_audio
        print(f"  Transcribing audio (FFT-based)...")
        events, bpm = transcribe_audio(input_path)
    else:
        print(f"  Unknown format: {ext}")
        return False

    if not events:
        print(f"  No events found in {input_path}")
        return False

    from .import_midi import events_to_e_source
    source = events_to_e_source(events, bpm, human=True)

    if not output:
        base = os.path.splitext(input_path)[0]
        output = base + ".e"

    with open(output, "w", encoding="utf-8") as f:
        f.write(source)
    sz = os.path.getsize(output) // 1024
    print(f"  ✓ {output} ({sz}KB, {len(events)} notes)")
    return True


def main():
    parser = argparse.ArgumentParser(description="E Language Compiler v4")
    parser.add_argument("command", choices=["compile", "play", "info", "import"])
    parser.add_argument("input", help="Input file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--bpm", type=float, help="Override BPM")
    parser.add_argument("--volume", type=float, help="Master volume 0.0-1.0")
    parser.add_argument("--effects", type=str, help="Audio effects key=val,key=val")
    parser.add_argument("--project", action="store_true", help="Import as full .ei project")
    parser.add_argument("--strict", action="store_true",
                        help="Fail fast on any syntax/diagnostic error (exit code 2)")

    args = parser.parse_args()

    if args.command == "compile":
        try:
            compile_file(args.input, args.output, volume=args.volume, bpm_override=args.bpm,
                         strict=args.strict)
        except Exception as e:
            if args.strict:
                print(f"  [STRICT FAIL] {e}", file=sys.stderr)
                sys.exit(2)
            raise

    elif args.command == "info":
        ext = os.path.splitext(args.input)[1].lower()
        if ext in (".ei", ".enx", ".eci"):
            events, bpm = compile_auto(args.input, args.bpm)
        else:
            with open(args.input, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            events, bpm = compile_source(text, args.bpm)
        print(f"File: {args.input}")
        print(f"Events: {len(events)}")
        print(f"BPM: {bpm}")
        if events:
            total_dur = max(e["timestamp"] + e["duration"] for e in events)
            notes = [e["midi"] for e in events]
            print(f"Duration: {total_dur / 1000:.2f}s")
            print(f"Note range: {min(notes)}-{max(notes)}")

    elif args.command == "import":
        import_file(args.input, args.output, project=args.project)

    elif args.command == "play":
        print(f"Playing: {args.input}")
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from player import main as player_main
        sys.argv = ["player.py", args.input]
        player_main()
