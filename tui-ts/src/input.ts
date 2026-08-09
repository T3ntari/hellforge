/** HELL'S CODE TypeScript TUI — raw input line handling.
 *
 *  Three layers:
 *  - `applyEditorKey` — pure editor core: typing, arrows, Home/End,
 *    backspace/delete, Ctrl+C copy / Ctrl+V paste / Ctrl+X cut, Enter
 *    submit with an EMPTY-INPUT GUARD (whitespace-only Enter is blocked,
 *    never submitted).
 *  - `copyText` / `readClipboard` — OS clipboard via child_process:
 *    wl-copy/wl-paste (Wayland) → xclip → xsel fallback. Silently no-ops
 *    when no clipboard tool is available (fully offline).
 *  - `useInputEditor` — Ink `useInput` hook wiring the core to keystrokes
 *    and the clipboard. Returns the editor state for rendering.
 *
 *  Note on Home/End: Ink 5.2's `useInput` swallows them (parseKeypress
 *  maps them to names that surface as an empty `input` and no key flags),
 *  so this module also listens on Ink's internal stdin event emitter and
 *  routes the escape sequences itself. `matchHomeEnd` is exported for that. */

import { useCallback, useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { spawnSync } from "node:child_process";
import { useInput, useStdin } from "ink";
import type { Key } from "ink";

// ── editor state ──

export interface EditorState {
  /** Current text of the input line. */
  buffer: string;
  /** Cursor position, 0..buffer.length. */
  cursor: number;
}

export function createEditorState(initial = ""): EditorState {
  return { buffer: initial, cursor: initial.length };
}

// ── editor events ──

/** What a keypress did. The hook performs the side effects; the core is
 *  pure and returns only intent. */
export type EditorEvent =
  | { kind: "none" }
  | { kind: "change"; state: EditorState }
  | { kind: "submit"; line: string }
  | { kind: "blocked" } // Enter with empty/whitespace input — guard tripped
  | { kind: "copy"; text: string }
  | { kind: "cut"; text: string; state: EditorState }
  | { kind: "paste" };

/** Ink's `Key` type has no Home/End (they are swallowed by its parser);
 *  the raw stdin listener delivers them as `{ home: true }` / `{ end: true }`. */
export interface EditorKey extends Partial<Key> {
  home?: boolean;
  end?: boolean;
}

// ── pure editor core ──

function change(buffer: string, cursor: number): EditorEvent {
  return { kind: "change", state: { buffer, cursor } };
}

function move(state: EditorState, delta: number): EditorEvent {
  const cursor = Math.max(0, Math.min(state.buffer.length, state.cursor + delta));
  return change(state.buffer, cursor);
}

/** Apply one raw keypress to the editor state. Pure: performs no I/O. */
export function applyEditorKey(state: EditorState, input: string, key: EditorKey): EditorEvent {
  // Enter — submit, but never an empty line (EMPTY-INPUT GUARD).
  if (key.return || input === "\r" || input === "\n") {
    if (state.buffer.trim().length === 0) {
      return { kind: "blocked" };
    }
    return { kind: "submit", line: state.buffer };
  }

  // Ctrl+chords: copy / cut / paste. Everything else Ctrl is ignored so it
  // can never leak into the buffer.
  if (key.ctrl && !key.meta) {
    switch (input.toLowerCase()) {
      case "c":
        return { kind: "copy", text: state.buffer };
      case "x":
        return {
          kind: "cut",
          text: state.buffer,
          state: { buffer: "", cursor: 0 },
        };
      case "v":
        return { kind: "paste" };
      default:
        return { kind: "none" };
    }
  }

  if (key.tab || key.escape) {
    return { kind: "none" };
  }

  if (key.home) {
    return change(state.buffer, 0);
  }
  if (key.end) {
    return change(state.buffer, state.buffer.length);
  }
  if (key.leftArrow) {
    return move(state, -1);
  }
  if (key.rightArrow) {
    return move(state, 1);
  }
  if (key.backspace) {
    if (state.cursor <= 0) {
      return { kind: "none" };
    }
    return change(state.buffer.slice(0, state.cursor - 1) + state.buffer.slice(state.cursor), state.cursor - 1);
  }
  if (key.delete) {
    if (state.cursor >= state.buffer.length) {
      return { kind: "none" };
    }
    return change(state.buffer.slice(0, state.cursor) + state.buffer.slice(state.cursor + 1), state.cursor);
  }

  // Typing — single-line input: newlines become spaces, stray control
  // characters are dropped.
  const text = input.replace(/\r?\n/g, " ").replace(/[\u0000-\u001f\u007f]/g, "");
  if (text.length === 0) {
    return { kind: "none" };
  }
  return change(
    state.buffer.slice(0, state.cursor) + text + state.buffer.slice(state.cursor),
    state.cursor + text.length,
  );
}

// ── Home/End escape sequences (Ink swallows these via useInput) ──

const HOME_SEQS = new Set(["\u001b[H", "\u001b[1~", "\u001b[7~", "\u001bOH", "\u001b[7$", "\u001b[7^"]);
const END_SEQS = new Set(["\u001b[F", "\u001b[4~", "\u001b[8~", "\u001bOF", "\u001b[8$", "\u001b[8^"]);
const HOME_MOD_RE = /^\u001b\[1;\d*H$/;
const END_MOD_RE = /^\u001b\[1;\d*F$/;

/** Map a raw stdin chunk to a Home/End key, or null if it is anything else. */
export function matchHomeEnd(chunk: string): EditorKey | null {
  if (HOME_SEQS.has(chunk) || HOME_MOD_RE.test(chunk)) {
    return { home: true };
  }
  if (END_SEQS.has(chunk) || END_MOD_RE.test(chunk)) {
    return { end: true };
  }
  return null;
}

// ── OS clipboard (child_process, wl-copy/xclip/xsel fallback) ──

const CLIP_TIMEOUT = 1500;
const CLIP_MAX_BUFFER = 1024 * 1024;

const CLIP_COPY: ReadonlyArray<readonly [string, readonly string[]]> = [
  ["wl-copy", []],
  ["xclip", ["-selection", "clipboard"]],
  ["xsel", ["-b", "-i"]],
];

const CLIP_READ: ReadonlyArray<readonly [string, readonly string[]]> = [
  ["wl-paste", ["--no-newline"]],
  ["xclip", ["-o", "-selection", "clipboard"]],
  ["xsel", ["-b", "-o"]],
];

/** Put `text` on the OS clipboard. Returns true if some tool succeeded. */
export function copyText(text: string): boolean {
  for (const [cmd, args] of CLIP_COPY) {
    try {
      const result = spawnSync(cmd, args, {
        input: text,
        timeout: CLIP_TIMEOUT,
        maxBuffer: CLIP_MAX_BUFFER,
      });
      if (!result.error && result.status === 0) {
        return true;
      }
    } catch {
      // Try the next tool.
    }
  }
  return false;
}

/** Read the OS clipboard. Returns "" when no tool is available or the
 *  clipboard is empty/unreadable. */
export function readClipboard(): string {
  for (const [cmd, args] of CLIP_READ) {
    try {
      const result = spawnSync(cmd, args, {
        encoding: "utf8",
        timeout: CLIP_TIMEOUT,
        maxBuffer: CLIP_MAX_BUFFER,
      });
      if (!result.error && result.status === 0 && typeof result.stdout === "string") {
        return result.stdout;
      }
    } catch {
      // Try the next tool.
    }
  }
  return "";
}

// ── Ink hook ──

export interface InputEditorOptions {
  /** Disable input handling entirely (e.g. while a gatekeeper ask is up). */
  isActive?: boolean;
  initial?: string;
  /** Called with the submitted line — never called with an empty/blank one. */
  onSubmit: (line: string) => void;
}

export interface InputEditor {
  state: EditorState;
  setState: Dispatch<SetStateAction<EditorState>>;
  clear: () => void;
  /** The most recent handled event (copy/cut/blocked/...), for UI feedback. */
  lastEvent: EditorEvent | null;
}

/** Ink `useInput` wiring: typing/arrows/Home/End/backspace, Ctrl+C copy,
 *  Ctrl+V paste, Ctrl+X cut, Enter submit with empty-input guard. */
export function useInputEditor({ isActive = true, initial, onSubmit }: InputEditorOptions): InputEditor {
  const [state, setState] = useState<EditorState>(() => createEditorState(initial ?? ""));
  const [lastEvent, setLastEvent] = useState<EditorEvent | null>(null);
  const stateRef = useRef(state);
  stateRef.current = state;
  const onSubmitRef = useRef(onSubmit);
  onSubmitRef.current = onSubmit;
  const { internal_eventEmitter } = useStdin();

  const apply = useCallback((ev: EditorEvent) => {
    try {
      import("node:fs").then(m => m.appendFileSync("/tmp/editor_ev.log",
        JSON.stringify({ kind: ev.kind, line: ev.kind === "submit" ? ev.line : undefined, buf: stateRef.current.buffer }) + "\n"));
    } catch {}
    switch (ev.kind) {
      case "change":
        setState(ev.state);
        stateRef.current = ev.state;  // keep the ref live between renders
        break;
      case "submit":
        onSubmitRef.current(ev.line);
        break;
      case "copy":
        copyText(ev.text);
        break;
      case "cut":
        copyText(ev.text);
        setState(ev.state);
        break;
      case "paste": {
        const text = readClipboard().replace(/\r?\n/g, " ");
        if (text.length === 0) {
          break;
        }
        const s = stateRef.current;
        setState({
          buffer: s.buffer.slice(0, s.cursor) + text + s.buffer.slice(s.cursor),
          cursor: s.cursor + text.length,
        });
        break;
      }
      case "blocked":
      case "none":
        break;
    }
    if (ev.kind !== "none") {
      setLastEvent(ev);
    }
  }, []);

  useInput(
    useCallback(
      (input, key) => {
        // Fast typing / paste can deliver several keys in ONE chunk (e.g.
        // "/exit\n" as a single sequence). Split it and apply each
        // character in order — the ref is synced on change, so the state
        // chains correctly.
        if (input && input.length > 1 && !key.ctrl && !key.meta) {
          for (const ch of input) {
            const k =
              ch === "\n" || ch === "\r"
                ? { return: true }
                : ch === "\x7f" || ch === "\b"
                  ? { backspace: true }
                  : ({} as Key);
            apply(applyEditorKey(stateRef.current, ch, k));
          }
          return;
        }
        apply(applyEditorKey(stateRef.current, input, key));
      },
      [apply],
    ),
    { isActive },
  );

  // Home/End — see module docstring; Ink's useInput cannot express them.
  useEffect(() => {
    if (!isActive) {
      return;
    }
    const onChunk = (chunk: unknown) => {
      const s =
        typeof chunk === "string" ? chunk : Buffer.isBuffer(chunk) ? chunk.toString("utf8") : "";
      const nav = matchHomeEnd(s);
      if (nav === null) {
        return;
      }
      apply(applyEditorKey(stateRef.current, "", nav));
    };
    internal_eventEmitter.on("input", onChunk);
    return () => {
      internal_eventEmitter.off("input", onChunk);
    };
  }, [isActive, internal_eventEmitter, apply]);

  const clear = useCallback(() => {
    setState(createEditorState(""));
  }, []);

  return { state, setState, clear, lastEvent };
}
