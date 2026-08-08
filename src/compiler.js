import { parse } from './parser.js';
import {
  noteToMidi, getChordSemitones, resolveQuality,
  parseDuration, parseVelocity, parseStrum
} from './music-theory.js';

export class Compiler {
  constructor() {
    this.files = {};
    this.defaultBpm = 120;
    this.defaultDur = 'quarter';
    this.defaultVel = 80;
  }

  registerFile(name, content) {
    this.files[name] = content;
  }

  async loadFile(path) {
    if (this.files[path]) return this.files[path];
    try {
      const resp = await fetch(path);
      if (!resp.ok) throw new Error(`Failed to load ${path}: ${resp.status}`);
      const text = await resp.text();
      this.files[path] = text;
      return text;
    } catch (e) {
      if (typeof window === 'undefined') {
        const fs = await import('fs');
        const text = fs.readFileSync(path, 'utf8');
        this.files[path] = text;
        return text;
      }
      throw e;
    }
  }

  stripComments(source) {
    return source.replace(/\/\/[^\n]*/g, '');
  }

  async resolveImports(source, baseDir, visited) {
    visited = visited || new Set();
    const importRegex = /import\s+"([^"]+)"/g;
    let match;
    let resolved = source;
    while ((match = importRegex.exec(source)) !== null) {
      const importPath = match[1];
      const fullPath = baseDir ? baseDir + '/' + importPath : importPath;
      if (visited.has(fullPath)) {
        resolved = resolved.replace(match[0], '');
        continue;
      }
      visited.add(fullPath);
      const importedSource = await this.loadFile(fullPath);
      const importDir = fullPath.includes('/') ? fullPath.substring(0, fullPath.lastIndexOf('/')) : baseDir;
      const finalSource = await this.resolveImports(importedSource, importDir, visited);
      resolved = resolved.replace(match[0], finalSource);
    }
    return resolved;
  }

  detectMode(source) {
    const human = /#HUMAN/i.test(source);
    const machine = /#MACHINE/i.test(source);
    if (human && machine) return 'mixed';
    if (machine) return 'machine';
    return 'human';
  }

  splitByMode(source) {
    const sections = [];
    const modeRegex = /#(HUMAN|MACHINE)\b/gi;
    let lastIndex = 0;
    let lastMode = 'human';
    let match;

    while ((match = modeRegex.exec(source)) !== null) {
      if (match.index > lastIndex) {
        sections.push({ mode: lastMode, text: source.slice(lastIndex, match.index).trim() });
      }
      lastMode = match[1].toLowerCase();
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < source.length) {
      sections.push({ mode: lastMode, text: source.slice(lastIndex).trim() });
    }
    return sections;
  }

  async compile(source, sourcePath) {
    const cleaned = this.stripComments(source);
    const baseDir = sourcePath ? (sourcePath.includes('/') ? sourcePath.substring(0, sourcePath.lastIndexOf('/')) : '') : '';
    const resolved = await this.resolveImports(cleaned, baseDir);
    const mode = this.detectMode(resolved);
    const sections = mode === 'mixed' ? this.splitByMode(resolved) : [{ mode, text: resolved.replace(/#(HUMAN|MACHINE)\b/gi, '').trim() }];

    let allEvents = [];
    let bpm = this.defaultBpm;

    for (const section of sections) {
      if (!section.text) continue;
      const events = section.mode === 'machine'
        ? this.compileMachine(section.text, bpm)
        : this.compileHuman(section.text, bpm);
      allEvents = allEvents.concat(events);
    }

    allEvents.sort((a, b) => a.timestamp - b.timestamp);
    return { events: allEvents, bpm };
  }

  compileHuman(source, bpm) {
    const ast = parse(source, { startRule: 'HumanStart' });
    const events = [];
    let cursor = 0;

    for (const stmt of ast) {
      const props = this.normalizeProps(stmt.props);
      const dur = parseDuration(props.dur || this.defaultDur, bpm) || parseDuration(this.defaultDur, bpm);
      const vel = parseVelocity(props.vel || '') || this.defaultVel;

      if (stmt.type === 'play_note') {
        const midi = noteToMidi(
          stmt.note.replace(/[0-9]/g, ''),
          stmt.note.replace(/[^0-9]/g, '')
        );
        events.push({ timestamp: cursor, midi, duration: dur, velocity: vel, fx: { pan: 0, bend: 0 } });
      } else if (stmt.type === 'play_chord') {
        const rootMidi = noteToMidi(
          stmt.root.replace(/[0-9]/g, ''),
          stmt.root.replace(/[^0-9]/g, '')
        );
        const quality = resolveQuality(stmt.quality);
        const semitones = getChordSemitones(rootMidi, quality);
        const strum = parseStrum(props.strum);

        semitones.forEach((midi, i) => {
          const offset = strum ? i * strum.time : 0;
          events.push({
            timestamp: cursor + offset,
            midi,
            duration: dur - offset,
            velocity: vel,
            fx: { pan: 0, bend: 0 }
          });
        });
      }

      cursor += dur;
    }

    return events;
  }

  compileMachine(source, bpm) {
    const ast = parse(source, { startRule: 'MachineStart' });
    const defaultDur = parseDuration(this.defaultDur, bpm);
    const events = [];

    for (const stmt of ast) {
      if (stmt.type !== 'machine_event') continue;
      const props = this.normalizeProps(stmt.props);
      const dur = parseDuration(props.dur) || defaultDur;
      const vel = parseVelocity(props.vel) !== null ? parseVelocity(props.vel) : this.defaultVel;

      events.push({
        timestamp: stmt.timestamp,
        midi: stmt.midi,
        duration: dur,
        velocity: vel,
        fx: {
          pan: stmt.fx && stmt.fx.pan !== undefined ? stmt.fx.pan : 0,
          bend: stmt.fx && stmt.fx.bend !== undefined ? stmt.fx.bend : 0,
        }
      });
    }

    return events;
  }

  normalizeProps(props) {
    const map = {};
    for (const p of (props || [])) {
      const key = p.name === 'velocity' ? 'vel' : p.name;
      map[key] = p.value;
    }
    return map;
  }
}
