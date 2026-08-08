"""Render MIDI to WAV/MP3 using the system MIDI synth + ffmpeg.
Usage: py -3 render_midi.py <input.mid> [output.wav]"""

import sys
import os
import subprocess
import tempfile

def render_midi(midi_path, output_path=None):
    """Render a MIDI file to WAV using pygame.sndarray + ffmpeg."""
    if not output_path:
        output_path = os.path.splitext(midi_path)[0] + ".wav"

    try:
        import pygame
        import numpy as np
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

        # Load MIDI as Sound object (pygame handles MIDI->audio internally)
        sound = pygame.mixer.Sound(midi_path)
        arr = pygame.sndarray.samples(sound)
        sample_rate = 44100

        # Play and wait for completion
        channel = sound.play()
        if channel:
            while channel.get_busy():
                pygame.time.wait(100)

        pygame.mixer.quit()

        # Write WAV from the pre-loaded array
        from scipy.io import wavfile
        wavfile.write(output_path, sample_rate, arr)
        print(f"  \u2713 {output_path}")

        # Convert to MP3 if ffmpeg available
        mp3_path = os.path.splitext(output_path)[0] + ".mp3"
        r = subprocess.run(["ffmpeg", "-y", "-i", output_path, "-b:a", "192k", mp3_path],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode == 0:
            os.unlink(output_path)
            print(f"  \u2713 {mp3_path}")
            return mp3_path
        return output_path
    except Exception as e:
        print(f"  pygame render failed: {e}")

    # Fallback: use ffmpeg directly
    print(f"  Using ffmpeg direct render...")
    out = output_path
    if not out.endswith(".mp3"):
        out = os.path.splitext(output_path)[0] + ".mp3"
    r = subprocess.run(["ffmpeg", "-y", "-i", midi_path, "-b:a", "192k", out],
                      capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if r.returncode == 0:
        print(f"  \u2713 {out}")
        return out
    print(f"  \u2717 ffmpeg failed")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -3 render_midi.py <input.mid> [output.wav]")
        print("  Renders MIDI to WAV/MP3 using system synth")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if not os.path.exists(inp):
        print(f"File not found: {inp}")
        sys.exit(1)
    render_midi(inp, out)
