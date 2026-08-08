export class AudioEngine {
  constructor() {
    this.sampler = null;
    this.panner = null;
    this.scheduledEvents = [];
    this.isPlaying = false;
    this._ready = false;
    this.onReady = null;
    this.onComplete = null;
  }

  async init() {
    await Tone.start();
    this._ready = false;
    this.sampler = new Tone.Sampler({
      urls: {
        'A0': 'A0.mp3', 'C1': 'C1.mp3', 'D#1': 'Ds1.mp3',
        'F#1': 'Fs1.mp3', 'A1': 'A1.mp3', 'C2': 'C2.mp3',
        'D#2': 'Ds2.mp3', 'F#2': 'Fs2.mp3', 'A2': 'A2.mp3',
        'C3': 'C3.mp3', 'D#3': 'Ds3.mp3', 'F#3': 'Fs3.mp3',
        'A3': 'A3.mp3', 'C4': 'C4.mp3', 'D#4': 'Ds4.mp3',
        'F#4': 'Fs4.mp3', 'A4': 'A4.mp3', 'C5': 'C5.mp3',
        'D#5': 'Ds5.mp3', 'F#5': 'Fs5.mp3', 'A5': 'A5.mp3',
        'C6': 'C6.mp3', 'D#6': 'Ds6.mp3', 'F#6': 'Fs6.mp3',
        'A6': 'A6.mp3', 'C7': 'C7.mp3', 'D#7': 'Ds7.mp3',
        'F#7': 'Fs7.mp3', 'A7': 'A7.mp3', 'C8': 'C8.mp3',
      },
      baseUrl: 'https://tonejs.github.io/audio/salamander/',
      onload: () => {
        this._ready = true;
        if (this.onReady) this.onReady();
      }
    }).toDestination();

    this.panner = new Tone.Panner(0).connect(Tone.Destination);
  }

  msToTransportTime(ms, bpm) {
    const beatMs = 60000 / bpm;
    const beats = ms / beatMs;
    const bars = Math.floor(beats / 4);
    const barBeats = Math.floor(beats % 4);
    const sixteenths = Math.round((beats - Math.floor(beats)) * 4);
    return `${bars}:${barBeats}:${sixteenths}`;
  }

  msToDuration(durMs) {
    if (durMs <= 0) return '0n';
    return durMs / 1000 + 's';
  }

  scheduleAll(events, bpm) {
    this.clearAll();
    Tone.Transport.bpm.value = bpm;
    Tone.Transport.stop();

    let maxEndTime = 0;

    for (const ev of events) {
      if (ev.timestamp === undefined) continue;

      const startTime = this.msToTransportTime(ev.timestamp, bpm);
      const durStr = this.msToDuration(ev.duration);
      const vel = Math.min(1, Math.max(0, (ev.velocity || 80) / 127));
      const endMs = ev.timestamp + ev.duration;
      if (endMs > maxEndTime) maxEndTime = endMs;

      const fx = ev.fx || {};
      const panVal = fx.pan !== undefined ? fx.pan : 0;
      const bend = fx.bend !== undefined ? fx.bend : 0;

      const id = Tone.Transport.schedule((time) => {
        if (!this._ready) return;

        let noteName = this.midiToTone(ev.midi);

        if (bend !== 0) {
          const bentMidi = ev.midi + bend / 100;
          noteName = this.midiToTone(Math.round(bentMidi));
        }

        try {
          const voice = this.sampler;
          if (panVal !== 0) {
            this.panner.pan.value = panVal;
          }
          voice.triggerAttackRelease(noteName, durStr, time, vel);
        } catch (e) {
          console.warn('Failed to play note:', ev.midi, e);
        }
      }, startTime);

      this.scheduledEvents.push(id);
    }

    const totalBeatEnd = (maxEndTime / (60000 / bpm)) + 2;
    const endBars = Math.floor(totalBeatEnd / 4);
    const endBeats = Math.floor(totalBeatEnd % 4);
    const endSixteenths = Math.round((totalBeatEnd - Math.floor(totalBeatEnd)) * 4);

    this.scheduledEvents.push(Tone.Transport.schedule(() => {
      if (this.onComplete) this.onComplete();
      Tone.Transport.stop();
      this.isPlaying = false;
    }, `${endBars}:${endBeats}:${endSixteenths}`));
  }

  midiToTone(midi) {
    const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const octave = Math.floor(midi / 12) - 1;
    const semitone = midi % 12;
    return names[semitone] + octave;
  }

  play() {
    if (this.isPlaying) return;
    this.isPlaying = true;
    Tone.Transport.start();
  }

  stop() {
    this.clearAll();
    Tone.Transport.stop();
    this.isPlaying = false;
  }

  clearAll() {
    for (const id of this.scheduledEvents) {
      try { Tone.Transport.clear(id); } catch (e) {}
    }
    this.scheduledEvents = [];
  }

  get loaded() {
    return this._ready;
  }
}
