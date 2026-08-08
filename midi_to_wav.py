"""Default MIDI → WAV/MP3 renderer. Uses FluidSynth, falls back to software synth.
This is the single entry point for ALL audio rendering in E.
Usage: py -3 midi_to_wav.py <input.mid> [output.wav]"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from piano_synth import render
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -3 midi_to_wav.py <input.mid> [output.wav]")
        sys.exit(1)
    inp = sys.argv[1]
    if not os.path.exists(inp):
        print(f"Not found: {inp}")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = render(inp, out)
    if result:
        print(f"Play: py -3 player.py \"{result}\"")
