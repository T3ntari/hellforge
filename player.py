#!/usr/bin/env python3
"""
E Glass Player — Custom glassmorphism media player for E Language outputs.
Supports .mid, .wav, .mp3, .mp4 playback with interactive timeline.

Controls:
  Space      Play/Pause
  ← →       Seek ±5s
  ↑ ↓       Volume ±10%
  Mouse      Click/drag on timeline, volume bar
  Esc/Ctrl+C Back to console
  exit       Quit player entirely
"""

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pygame
import pygame.midi
import subprocess
import sys
import tempfile
import time
import math
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
EP_PATH = PROJECT_DIR / "ep.py"

# ── Colors (Glassmorphism palette) ───────────

BG_DARK = (18, 18, 30)
GLASS_BG = (30, 30, 50, 180)
GLASS_BORDER = (60, 60, 90, 100)
ACCENT = (100, 180, 255)
ACCENT2 = (180, 100, 255)
TEXT = (220, 220, 240)
TEXT_DIM = (140, 140, 170)
RED = (255, 80, 80)
GREEN = (80, 255, 120)
YELLOW = (255, 220, 80)
PROGRESS = (100, 180, 255)
VOLUME_COLOR = (80, 255, 120)


def draw_glass_panel(surf, rect, radius=12, border=True):
    """Draw a glassmorphism panel."""
    r = pygame.Rect(rect)
    # Main bg
    s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(s, GLASS_BG, s.get_rect(), border_radius=radius)
    # Border
    if border:
        pygame.draw.rect(s, GLASS_BORDER, s.get_rect(), width=1, border_radius=radius)
    surf.blit(s, r)


def draw_rounded_bar(surf, rect, pct, color, bg_color=(40, 40, 60)):
    """Draw a horizontal progress bar with rounded ends."""
    r = pygame.Rect(rect)
    rad = r.h // 2
    pygame.draw.rect(surf, bg_color, r, border_radius=rad)
    if pct > 0:
        fill_r = pygame.Rect(r.x, r.y, int(r.w * pct), r.h)
        pygame.draw.rect(surf, color, fill_r, border_radius=rad)


def format_time(secs):
    """Format seconds to mm:ss."""
    m = int(secs // 60)
    s = int(secs % 60)
    return f"{m}:{s:02d}"


class EPlayer:
    def __init__(self, path):
        self.path = path
        self.ext = os.path.splitext(path)[1].lower()
        self.duration = 0
        self.position = 0.0
        self.volume = 0.7
        self.playing = False
        self.paused = False
        self.done = False
        self.return_to_console = False
        self.start_time = 0
        self.pause_time = 0

        # For MIDI playback via pygame.midi
        self.midi_player = None
        self.midi_out = None
        self.midi_events = []
        self.midi_start_time = 0
        self.midi_index = 0

        # For WAV/MP3 playback
        self.audio_file = None
        self.audio_playing = False

        # For MP4 video
        self.video_process = None
        self.video_surf = None
        self.video_paused = False

        # UI
        self.width = 900
        self.height = 550
        self.running = True
        self.drag_timeline = False

    def load(self):
        """Load the media file."""
        if self.ext == ".mid":
            self._load_midi()
        elif self.ext in (".wav", ".mp3"):
            self._load_audio()
        elif self.ext == ".mp4":
            self._load_video()
        else:
            # Try to compile .e/.eic to .mid first
            mid_path = tempfile.mktemp(suffix=".mid")
            r = subprocess.run(
                [sys.executable, str(EP_PATH), "compile", self.path, "-o", mid_path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
            )
            if r.returncode == 0:
                self.path = mid_path
                self.ext = ".mid"
                self._load_midi()
            else:
                # Fall back to WAV
                wav_path = tempfile.mktemp(suffix=".wav")
                r2 = subprocess.run(
                    [sys.executable, str(EP_PATH), "compile", self.path, "-o", wav_path],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
                )
                if r2.returncode == 0:
                    self.path = wav_path
                    self.ext = ".wav"
                    self._load_audio()
                else:
                    print(f"Error: cannot play {self.path}")
                    self.done = True

    def _load_midi(self):
        """Parse MIDI events for real-time playback."""
        import mido
        mid = mido.MidiFile(self.path)
        self.duration = mid.length
        self.midi_events = []
        t = 0
        for msg in mid:
            t += msg.time
            if msg.type in ("note_on", "note_off"):
                self.midi_events.append((t, msg))
        self.playing = True

    def _load_audio(self):
        """Load WAV/MP3 for playback."""
        try:
            from ep_audio import audio_config
            cfg = audio_config.apply_to_player()
            pygame.mixer.init(**cfg)
        except Exception:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        try:
            pygame.mixer.music.load(self.path)
            self.duration = self._get_audio_duration()
            self.playing = True
        except Exception as e:
            print(f"Audio load error: {e}")
            self.done = True

    def _get_audio_duration(self):
        """Get audio duration using ffprobe."""
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", self.path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            return float(r.stdout.strip())
        except Exception:
            return 0

    def _load_video(self):
        """Load MP4 video via ffmpeg pipe."""
        self.duration = self._get_audio_duration()
        self.playing = True

    def handle_events(self):
        """Process pygame events."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                self.done = True

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                    self.return_to_console = True
                elif ev.key == pygame.K_SPACE:
                    self._toggle_pause()
                elif ev.key == pygame.K_RIGHT:
                    self._seek(5)
                elif ev.key == pygame.K_LEFT:
                    self._seek(-5)
                elif ev.key == pygame.K_UP:
                    self._change_volume(0.1)
                elif ev.key == pygame.K_DOWN:
                    self._change_volume(-0.1)
                elif ev.key == pygame.K_RETURN:
                    self._toggle_pause()

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                x, y = ev.pos
                # Timeline bar
                tl_rect = pygame.Rect(60, self.height - 90, self.width - 120, 14)
                if tl_rect.collidepoint(x, y):
                    self.drag_timeline = True
                    self._seek_to_pct((x - tl_rect.x) / tl_rect.w)
                # Volume bar
                vol_rect = pygame.Rect(self.width - 160, 35, 120, 12)
                if vol_rect.collidepoint(x, y):
                    self._change_volume_to((x - vol_rect.x) / vol_rect.w)

            elif ev.type == pygame.MOUSEBUTTONUP:
                self.drag_timeline = False

            elif ev.type == pygame.MOUSEMOTION:
                if self.drag_timeline:
                    tl_rect = pygame.Rect(60, self.height - 90, self.width - 120, 14)
                    x = max(tl_rect.x, min(ev.pos[0], tl_rect.x + tl_rect.w))
                    self._seek_to_pct((x - tl_rect.x) / tl_rect.w)

    def _toggle_pause(self):
        if self.ext == ".mid":
            self.paused = not self.paused
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.paused = True
            else:
                pygame.mixer.music.unpause()
                self.paused = False

    def _seek(self, seconds):
        if self.ext in (".wav", ".mp3"):
            pos = self.position + seconds
            pos = max(0, min(pos, self.duration))
            pygame.mixer.music.play(start=pos)
            self.position = pos

    def _seek_to_pct(self, pct):
        target = pct * self.duration
        if self.ext in (".wav", ".mp3"):
            pygame.mixer.music.play(start=target)
        self.position = target

    def _change_volume(self, delta):
        self.volume = max(0, min(1, self.volume + delta))
        if self.ext in (".wav", ".mp3"):
            pygame.mixer.music.set_volume(self.volume)

    def _change_volume_to(self, val):
        self.volume = max(0, min(1, val))
        if self.ext in (".wav", ".mp3"):
            pygame.mixer.music.set_volume(self.volume)

    def update(self):
        """Update playback position."""
        if self.ext == ".mid":
            if self.paused:
                return
            dt = time.time() - self.midi_start_time
            self.position = dt
            if dt >= self.duration:
                self.running = False
        else:
            if pygame.mixer.music.get_busy() and not self.paused:
                self.position = self._get_audio_pos()

    def _get_audio_pos(self):
        """Get current playback position."""
        try:
            return pygame.mixer.music.get_pos() / 1000.0
        except Exception:
            return self.position

    def draw(self, surf):
        """Render the glassmorphism UI."""
        w, h = self.width, self.height

        # Background
        surf.fill(BG_DARK)

        # ── Album art area (glass) ──
        draw_glass_panel(surf, (30, 30, w - 60, h - 60), radius=20)

        # ── Title ──
        title = os.path.basename(self.path)
        font_big = pygame.font.SysFont("segoeui", 22, bold=True)
        ts = font_big.render(title, True, TEXT)
        surf.blit(ts, (80, 50))

        # ── Status ──
        font_small = pygame.font.SysFont("segoeui", 14)
        status = "▶ Playing" if not self.paused else "⏸ Paused"
        st = font_small.render(status, True, GREEN if not self.paused else YELLOW)
        surf.blit(st, (80, 80))

        # ── Time / Duration ──
        current_str = format_time(self.position)
        total_str = format_time(self.duration)
        time_font = pygame.font.SysFont("segoeui", 16)
        ct = time_font.render(current_str, True, TEXT)
        tt = time_font.render(total_str, True, TEXT_DIM)
        surf.blit(ct, (65, h - 112))
        surf.blit(tt, (w - 85, h - 112))

        # ── Timeline bar (glass) ──
        tl_rect = pygame.Rect(60, h - 90, w - 120, 14)
        pct = self.position / max(self.duration, 1)
        draw_rounded_bar(surf, tl_rect, pct, PROGRESS)
        # Dot on progress
        dot_x = int(tl_rect.x + tl_rect.w * pct)
        dot_y = tl_rect.y + tl_rect.h // 2
        pygame.draw.circle(surf, (180, 220, 255), (dot_x, dot_y), 8)
        pygame.draw.circle(surf, (255, 255, 255), (dot_x, dot_y), 4)

        # ── Controls ──
        ctrl_y = h - 55
        font_ctrl = pygame.font.SysFont("segoeui", 13)
        controls = [
            ("⏮ -5", "<-"),
            ("▶⏸", "SPACE"),
            ("⏭ +5", "->"),
            ("⏹ ESC", "ESC"),
        ]
        x_start = w // 2 - 180
        for label, key in controls:
            draw_glass_panel(surf, (x_start, ctrl_y, 80, 28), radius=8, border=False)
            lbl = font_ctrl.render(label, True, TEXT)
            surf.blit(lbl, (x_start + 10, ctrl_y + 6))
            x_start += 95

        # ── Volume (glass) ──
        vol_label = font_small.render(f"Vol: {int(self.volume * 100)}%", True, TEXT)
        surf.blit(vol_label, (w - 210, 38))
        vol_rect = pygame.Rect(w - 160, 40, 120, 12)
        draw_rounded_bar(surf, vol_rect, self.volume, VOLUME_COLOR)
        vdot_x = int(vol_rect.x + vol_rect.w * self.volume)
        pygame.draw.circle(surf, (180, 255, 200), (vdot_x, vol_rect.y + 6), 6)

        # ── Glass reflection overlay ──
        reflection = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(reflection, (255, 255, 255, 15),
                           (w // 2 - 200, -50, 400, h // 2))
        surf.blit(reflection, (0, 0))

        # ── Bottom hint ──
        hint = font_small.render("Ctrl+Z / Esc: back to console   |   exit: quit player", True, TEXT_DIM)
        surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 22))

    def run(self):
        """Main loop."""
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        pygame.init()
        pygame.display.set_caption("E Glass Player")
        screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        clock = pygame.time.Clock()

        self.load()
        if self.done:
            pygame.quit()
            return

        # Start playback
        if self.ext in (".wav", ".mp3"):
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
        elif self.ext == ".mid":
            pygame.midi.init()
            self.midi_out = _open_midi_output()
            self.midi_out.set_instrument(0, 0)
            # Kill reverb/chorus effects on all channels
            for ch in range(16):
                self.midi_out.write_short(0xB0 | ch, 91, 0)
                self.midi_out.write_short(0xB0 | ch, 93, 0)
            self.midi_start_time = time.time()
            self.midi_index = 0

        self.midi_start_time = time.time()

        while self.running:
            dt = clock.tick(60)

            # MIDI playback
            if self.ext == ".mid" and self.playing and not self.paused and self.midi_events:
                now = time.time() - self.midi_start_time
                while self.midi_index < len(self.midi_events) and self.midi_events[self.midi_index][0] <= now:
                    t, msg = self.midi_events[self.midi_index]
                    if msg.type == "note_on" and msg.velocity > 0:
                        self.midi_out.note_on(msg.note, msg.velocity, msg.channel)
                    elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                        self.midi_out.note_off(msg.note, 0, msg.channel)
                    self.midi_index += 1
                if self.midi_index >= len(self.midi_events):
                    self.position = self.duration
                    time.sleep(0.5)
                    self.running = False

            self.handle_events()
            self.update()
            self.draw(screen)
            pygame.display.flip()

        # Cleanup
        if self.midi_out:
            self.midi_out.close()
        pygame.midi.quit()
        pygame.mixer.music.stop()
        pygame.quit()

        if self.return_to_console:
            print("\n  > Back to console. Type 'exit' to quit player entirely.")
            # Mini interactive console
            while True:
                try:
                    cmd = input("  > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if cmd in ("exit", "quit"):
                    break
                elif cmd in ("play", "resume"):
                    self.paused = False
                    pygame.mixer.music.unpause()
                elif cmd == "pause":
                    self.paused = True
                    pygame.mixer.music.pause()
                else:
                    print(f"  Unknown: {cmd}. Try: exit, play, pause")


# ── Console Player (Terminal Mode) ────────────

class ConsolePlayer:
    """Full terminal-based player — no pygame window needed."""

    def __init__(self, path):
        self.path = path
        self.duration = 0
        self.position = 0.0
        self.volume = self._load_volume()
        self.paused = False
        self.running = True
        self.start_time = 0.0
        self.seek_flag = False
        self._is_audio = False

    def _save_volume(self):
        try:
            vol_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".player_volume.json")
            import json as _j
            with open(vol_file, "w") as f:
                _j.dump({"volume": self.volume}, f)
        except Exception:
            pass

    def _load_volume(self):
        try:
            vol_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".player_volume.json")
            if os.path.exists(vol_file):
                import json as _j
                with open(vol_file) as f:
                    return _j.load(f).get("volume", 0.7)
        except Exception:
            pass
        return 0.7

    def _fmt(self, s):
        return f"{int(s//60)}:{int(s%60):02d}"

    def _draw_timeline(self, width=50):
        pct = self.position / max(self.duration, 1)
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        return f"\033[36m{bar}\033[0m"

    def _clear_line(self):
        return "\033[K"

    def _run_midi(self):
        import mido
        mid = mido.MidiFile(self.path)
        self.duration = mid.length

        pygame.midi.init()
        self.midi_out = _open_midi_output()
        self.midi_out.set_instrument(0, 0)
        # Set initial volume on all channels
        self._send_volume_all_channels()
        # Kill reverb/chorus effects on all channels (Microsoft GS Wavetable fix)
        for ch in range(16):
            self.midi_out.write_short(0xB0 | ch, 91, 0)   # Reverb off
            self.midi_out.write_short(0xB0 | ch, 93, 0)   # Chorus off

        import threading
        stop_flag = [False]
        pause_lock = [False]

        def playback():
            for msg in mid:
                if stop_flag[0]:
                    break
                while pause_lock[0] and not stop_flag[0]:
                    time.sleep(0.05)
                if stop_flag[0]:
                    break
                if msg.time > 0:
                    time.sleep(msg.time)
                if not msg.is_meta and hasattr(msg, 'note'):
                    if msg.type == "note_on" and msg.velocity > 0:
                        scaled_vel = max(1, min(127, int(msg.velocity * self.volume)))
                        self.midi_out.note_on(msg.note, scaled_vel, msg.channel)
                    elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                        self.midi_out.note_off(msg.note, 0, msg.channel)

        t = threading.Thread(target=playback, daemon=True)
        t.start()

        self.start_time = time.time()
        paused_time = 0
        try:
            while t.is_alive() and self.running:
                if self.paused:
                    pause_lock[0] = True
                    if paused_time == 0:
                        paused_time = time.time()
                        self._send_volume_all_channels()  # volume 0 to mute
                    time.sleep(0.1)
                    self._display()
                    if sys.stdin.isatty():
                        import msvcrt
                        if msvcrt.kbhit():
                            k = msvcrt.getwch()
                            self._handle_key(k)
                    continue
                else:
                    pause_lock[0] = False
                    if paused_time > 0:
                        self.start_time += time.time() - paused_time
                        paused_time = 0
                    self._send_volume_all_channels()

                if self.seek_flag:
                    self.seek_flag = False
                    self.start_time = time.time() - self.position
                elapsed = time.time() - self.start_time
                self.position = min(elapsed, self.duration)
                self._display()
                if sys.stdin.isatty():
                    import msvcrt
                    if msvcrt.kbhit():
                        k = msvcrt.getwch()
                        self._handle_key(k)
                time.sleep(0.05)
        except KeyboardInterrupt:
            stop_flag[0] = True
            print()
            pass

        stop_flag[0] = True
        self.midi_out.close()
        pygame.midi.quit()

    def _run_audio(self):
        import pygame as pg
        pg.mixer.init(frequency=44100)
        pg.mixer.music.load(self.path)
        pg.mixer.music.set_volume(self.volume)
        pg.mixer.music.play()
        self.duration = self._get_duration()

        import select
        try:
            while pg.mixer.music.get_busy() and self.running:
                self.position = pg.mixer.music.get_pos() / 1000
                self._display()
                if sys.stdin.isatty():
                    import msvcrt
                    if msvcrt.kbhit():
                        k = msvcrt.getwch()
                        self._handle_key_audio(k)
                time.sleep(0.1)
        except KeyboardInterrupt:
            pg.mixer.music.stop()

    def _get_duration(self):
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", self.path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            return float(r.stdout.strip())
        except Exception:
            return 0

    def _display(self):
        tl = self._draw_timeline()
        pos = self._fmt(self.position)
        dur = self._fmt(self.duration)
        pct = int(self.position / max(self.duration, 1) * 100)
        vol = int(self.volume * 100)
        status = "▶" if not self.paused else "⏸"
        sys.stdout.write(f"\r{status} {pos}/{dur} [{tl}] {pct}%  Vol:{vol}%  {self._clear_line()}")
        sys.stdout.flush()

    def _send_volume_all_channels(self):
        """Send MIDI CC 7 (volume) on all 16 channels."""
        if not hasattr(self, 'midi_out') or not self.midi_out:
            return
        vol_cc = max(0, min(127, int(self.volume * 127)))
        for ch in range(16):
            self.midi_out.write_short(0xB0 | ch, 7, vol_cc)

    def _handle_key(self, k):
        import msvcrt
        if k in ("q", "Q", "\x1b"):
            self.running = False
        elif k == " ":
            self.paused = not self.paused
        elif k in ("\xe0", "\x00"):
            # Arrow keys: \xe0 or \x00 prefix on Windows
            k2 = msvcrt.getwch()
            if k2 in ("M", "m", "C"):          # Right
                self.position = min(self.position + 5, self.duration)
            elif k2 in ("K", "k", "D"):        # Left
                self.position = max(self.position - 5, 0)
        elif k in ("+", "="):
            self.volume = min(1, self.volume + 0.1)
            self._send_volume_all_channels()
            self._save_volume()
        elif k == "-":
            self.volume = max(0, self.volume - 0.1)
            self._send_volume_all_channels()
            self._save_volume()

    def _handle_key_audio(self, k):
        import msvcrt
        import pygame as pg
        if k in ("q", "Q", "\x1b"):
            self.running = False
        elif k == " ":
            if self.paused:
                pg.mixer.music.unpause()
            else:
                pg.mixer.music.pause()
            self.paused = not self.paused
        elif k in ("\xe0", "\x00"):
            k2 = msvcrt.getwch()
            if k2 in ("M", "m", "C"):
                self.position = min(self.position + 5, self.duration)
                pg.mixer.music.play(start=self.position)
            elif k2 in ("K", "k", "D"):
                self.position = max(self.position - 5, 0)
                pg.mixer.music.play(start=self.position)
        elif k in ("+", "="):
            self.volume = min(1, self.volume + 0.1)
            pg.mixer.music.set_volume(self.volume)
            self._save_volume()
        elif k == "-":
            self.volume = max(0, self.volume - 0.1)
            pg.mixer.music.set_volume(self.volume)
            self._save_volume()

    def run(self):
        print(f"\n  \033[1mE Console Player\033[0m — \033[90m{os.path.basename(self.path)}\033[0m")
        print(f"  \033[90m[Space] pause  [←→] seek ±5s  [+/-] vol  [q/Esc] quit\033[0m\n")

        ext = os.path.splitext(self.path)[1].lower()
        self._is_audio = ext in (".wav", ".mp3", ".mp4")
        if self._is_audio:
            self._run_audio()
        else:
            self._run_midi()

        print(f"\n  \033[92mDone.\033[0m")


# ── Entry Point ─────────────────────────────

def main():
    use_gui = "--gui" in sys.argv or "-g" in sys.argv

    if len(sys.argv) < 2 or sys.argv[1] in ("--gui", "-g"):
        # No file given — open file picker or show last played
        last = os.path.join(PROJECT_DIR, "ai_generated")
        print(f"  \033[1mE Glass Player\033[0m")
        print(f"  Drop a file on player.py or pass path as argument.")
        print(f"  Recent files in {last}:")
        if os.path.isdir(last):
            for f in sorted(os.listdir(last))[:5]:
                fp = os.path.join(last, f)
                if os.path.isdir(fp):
                    print(f"    {f}/")
        print(f"\n  Usage: python player.py <file.e/.mid/.wav/.mp3/.mp4/.eic>")
        if use_gui:
            print(f"  \033[90m(GUI mode selected but no file provided)\033[0m")
        sys.exit(1)

    raw_path = sys.argv[1]
    if not os.path.exists(raw_path):
        print(f"Error: file not found: {raw_path}")
        sys.exit(1)

    # Compile .e/.ei/.eic to MIDI first (original working path)
    ext = os.path.splitext(raw_path)[1].lower()
    if ext not in (".mid", ".wav", ".mp3", ".mp4"):
        print(f"  > Compiling {os.path.basename(raw_path)} to MIDI...")
        mid_path = tempfile.mktemp(suffix=".mid")
        my_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run(
            [sys.executable, str(EP_PATH), "compile", raw_path, "-o", mid_path],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, env=my_env,
        )
        if r.returncode == 0:
            path = mid_path
        else:
            print(f"  > Error: cannot compile {raw_path}")
            sys.exit(1)
    else:
        path = raw_path

    use_gui = "--gui" in sys.argv

    if use_gui:
        player = EPlayer(path)
        player.run()
    else:
        player = ConsolePlayer(path)
        player.run()


def _open_midi_output():
    """Open the first available MIDI output device, trying index 1 (GS Wavetable) first."""
    import pygame
    try:
        return pygame.midi.Output(1)
    except Exception:
        pass
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        if info and info[3] == 1:
            try:
                return pygame.midi.Output(i)
            except Exception:
                continue
    raise RuntimeError("No MIDI output device available")


if __name__ == "__main__":
    main()
