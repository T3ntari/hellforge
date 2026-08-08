import { Compiler } from './compiler.js';
import { AudioEngine } from './audio-engine.js';

const engine = new AudioEngine();
const compiler = new Compiler();

const sourceInput = document.getElementById('source');
const playBtn = document.getElementById('playBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const tempoInput = document.getElementById('tempo');

let currentEvents = [];

function setStatus(msg, isError) {
  statusEl.textContent = msg;
  statusEl.className = isError ? 'error' : '';
}

async function compileSource() {
  const source = sourceInput.value;
  if (!source.trim()) {
    setStatus('No source code to compile.', true);
    return null;
  }

  try {
    setStatus('Compiling...');
    const { events, bpm } = await compiler.compile(source, 'main.e');
    currentEvents = events;

    if (tempoInput) {
      tempoInput.value = bpm;
    }

    const noteCount = events.length;
    const totalMs = events.length > 0 ? Math.max(...events.map(e => e.timestamp + e.duration)) : 0;
    const totalSec = (totalMs / 1000).toFixed(1);
    setStatus(`Compiled OK — ${noteCount} note(s), ${bpm} BPM, ${totalSec}s`);
    return { events, bpm };
  } catch (err) {
    setStatus(`Compile error: ${err.message}`, true);
    console.error(err);
    return null;
  }
}

async function onPlay() {
  if (engine.isPlaying) return;
  if (!engine.loaded) {
    setStatus('Loading piano samples...');
    try {
      await Tone.start();
      await new Promise((resolve) => {
        engine.onReady = resolve;
        if (!engine.sampler) engine.init();
      });
    } catch (err) {
      setStatus(`Failed to load audio: ${err.message}`, true);
      return;
    }
  }

  const result = await compileSource();
  if (!result || result.events.length === 0) {
    setStatus('Nothing to play.', true);
    return;
  }

  const bpm = parseInt(tempoInput.value, 10) || result.bpm;
  engine.scheduleAll(result.events, bpm);
  engine.onComplete = () => setStatus('Playback complete.');
  engine.play();
  setStatus(`Playing ${result.events.length} note(s)...`);
}

function onStop() {
  engine.stop();
  setStatus('Stopped.');
}

function loadExample(name) {
  switch (name) {
    case 'human_basic':
      sourceInput.value = `#HUMAN

play note(C4) @dur:q
play note(D4) @dur:q
play note(E4) @dur:q
play note(F4) @dur:q
play note(G4) @dur:q
play note(A4) @dur:q
play note(B4) @dur:q
play note(C5) @dur:h`;
      break;
    case 'human_chords':
      sourceInput.value = `#HUMAN

play chord(C, major) @dur:h @vel:normal
play chord(D, minor) @dur:h @vel:normal
play chord(E, minor) @dur:h @vel:normal
play chord(F, major) @dur:h @vel:normal
play chord(G, major) @dur:h @vel:normal
play chord(C, major) @dur:w @vel:ff`;
      break;
    case 'human_strum':
      sourceInput.value = `#HUMAN

// Strummed chords with velocity dynamics
play chord(C, major) @dur:h @vel:80 @strum:down(15ms)
play chord(G, major) @dur:h @vel:90 @strum:down(15ms)
play chord(A, minor) @dur:h @vel:70 @strum:down(20ms)
play chord(F, major) @dur:h @vel:85 @strum:down(15ms)`;
      break;
    case 'machine_basic':
      sourceInput.value = `#MACHINE

// Basic arpeggio with absolute timestamps
T0    N60 D250 V0.7
T250  N64 D250 V0.7
T500  N67 D250 V0.7
T750  N72 D250 V0.7
T1000 N76 D250 V0.7
T1250 N79 D250 V0.7
T1500 N72 D250 V0.7
T1750 N67 D250 V0.7`;
      break;
    case 'machine_fx':
      sourceInput.value = `#MACHINE

// Notes with pitch bend and pan effects
T0    N60 D500 V0.8 P[bend:0]   S[pan:-0.5]
T500  N64 D500 V0.8 P[bend:0]   S[pan:-0.25]
T1000 N67 D500 V0.8 P[bend:0]   S[pan:0]
T1500 N72 D500 V0.8 P[bend:0]   S[pan:0.25]
T2000 N76 D500 V0.8 P[bend:-12] S[pan:0.5]
T2500 N79 D500 V0.8 P[bend:-12] S[pan:0.25]
T3000 N72 D500 V0.8 P[bend:0]   S[pan:0]
T3500 N67 D500 V0.8 P[bend:0]   S[pan:-0.25]`;
      break;
    case 'merged':
      compiler.registerFile('bassline.e', `#MACHINE
T0    N48 D500 V0.6
T500  N43 D500 V0.6
T1000 N45 D500 V0.6
T1500 N40 D500 V0.6
T2000 N48 D500 V0.8
T2500 N43 D500 V0.8
T3000 N45 D500 V0.8
T3500 N40 D500 V0.8`);
      sourceInput.value = `// Dual-mode composition: #HUMAN melody + #MACHINE bassline
import "bassline.e"

#HUMAN

// Right hand melody (starts at beat 1)
play note(C4) @dur:e @vel:80
play note(D4) @dur:e @vel:80
play note(E4) @dur:e @vel:80
play note(F4) @dur:e @vel:80
play note(G4) @dur:q @vel:85
play note(A4) @dur:q @vel:85
play note(B4) @dur:q @vel:85
play note(C5) @dur:h @vel:ff

#MACHINE

// Accent chords on strong beats
T0    N60 D800 V0.3
T2000 N67 D800 V0.3
T4000 N72 D800 V0.3`;
      break;
    case 'rush_e':
      sourceInput.value = `// "Rush E" inspired AI-friendly machine mode
#MACHINE

// Fast repeating pattern - 16th notes at 140 BPM
T0    N76 D100 V0.9
T100  N79 D100 V0.9
T200  N83 D100 V0.9
T300  N76 D100 V0.9
T400  N79 D100 V0.9
T500  N83 D100 V0.9
T600  N76 D100 V0.9
T700  N79 D100 V0.9

// Heavy chord stab
T800  N60 D400 V1.0 S[pan:-0.5]
T800  N64 D400 V1.0 S[pan:0]
T800  N67 D400 V1.0 S[pan:0.5]
T800  N72 D400 V0.8

// Run
T1200 N76 D80  V0.9
T1300 N79 D80  V0.9
T1400 N84 D80  V0.9
T1500 N88 D80  V0.9
T1600 N91 D80  V0.9
T1700 N88 D80  V0.9
T1800 N84 D80  V0.9
T1900 N79 D80  V0.9

// Final slam
T2000 N60 D1000 V1.0
T2000 N64 D1000 V1.0
T2000 N67 D1000 V1.0
T2000 N72 D1000 V1.0
T2000 N76 D1000 V1.0`;
      break;
    case 'rush_e_full':
      setStatus('Loading Rush E (20,141 notes)...');
      fetch('examples/Rush_E.e')
        .then(r => r.text())
        .then(text => {
          sourceInput.value = text;
          setStatus('Loaded Rush E — ready to play');
          if (!engine.isPlaying) compileSource();
        })
        .catch(err => setStatus(`Failed to load Rush E: ${err.message}`, true));
      return; // don't auto-compile yet, wait for fetch
  }
  setStatus(`Loaded example: ${name}`);
  if (!engine.isPlaying) {
    compileSource();
  }
}

playBtn.addEventListener('click', onPlay);
stopBtn.addEventListener('click', onStop);

document.querySelectorAll('[data-example]').forEach(btn => {
  btn.addEventListener('click', () => loadExample(btn.dataset.example));
});

setTimeout(compileSource, 100);
