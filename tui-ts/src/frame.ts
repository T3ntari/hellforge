/** Pure engine helpers for the HELL'S CODE TUI: feed reducer, word wrap,
 *  scroll math, tool-action tracking, and palette-token -> ANSI conversion.
 *  No React here — everything is a plain function the components import. */
import type { Color, FeedItem } from "./protocol.js";

// ── palette tokens -> ANSI ──────────────────────────
export const TOKENS: Record<Color, string> = {
  accent: "#FF4D4D",
  accent2: "#FF8A5C",
  text: "#F2E5DE",
  dim: "#8A7A74",
  ok: "#7EDC8F",
  err: "#FF6B6B",
  warn: "#FFD166",
};

const RE_ANSI = /\x1b\[[0-9;]*m/g;

export function stripAnsi(s: string): string {
  return s.replace(RE_ANSI, "");
}

/** Wrap text in a 24-bit foreground ANSI escape for a palette token.
 *  Returns the text unchanged when color is null/undefined. */
export function ansi(color: Color | null | undefined, text: string): string {
  if (!color) return text;
  const hex = TOKENS[color];
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `\x1b[38;2;${r};${g};${b}m${text}\x1b[39m`;
}

// ── feed reducer ────────────────────────────────────
export type FeedAction =
  | { type: "append"; item: FeedItem }
  | { type: "chunk"; text: string; color: Color | null }
  | { type: "clear" };

/** Feed state machine: `feed` events append whole items; `chunk` events
 *  stream text into the trailing item (or start a new one) so streaming
 *  responses render as one growing line. */
export function feedReducer(state: FeedItem[], action: FeedAction): FeedItem[] {
  switch (action.type) {
    case "clear":
      return [];
    case "append":
      return [...state, action.item];
    case "chunk": {
      if (!action.text) return state;
      if (state.length === 0) return [{ color: action.color, text: action.text }];
      const last = state[state.length - 1];
      if (last.color !== action.color) {
        return [...state, { color: action.color, text: action.text }];
      }
      return [...state.slice(0, -1), { color: last.color, text: last.text + action.text }];
    }
  }
}

// ── word wrap ───────────────────────────────────────
/** Greedy word wrap; words longer than the width are hard-split. */
export function wrap(text: string, width: number): string[] {
  if (width <= 0) return [];
  const out: string[] = [];
  for (const para of text.split("\n")) {
    if (para === "") {
      out.push("");
      continue;
    }
    let line = "";
    for (const word of para.split(" ")) {
      const token = line === "" ? word : ` ${word}`;
      if (line !== "" && line.length + token.length > width) {
        out.push(line);
        line = word;
      } else {
        line += token;
      }
      while (line.length > width) {
        out.push(line.slice(0, width));
        line = line.slice(width);
      }
    }
    out.push(line);
  }
  return out;
}

// ── scroll math ─────────────────────────────────────
export function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

export function maxScroll(total: number, height: number): number {
  return total > height ? total - height : 0;
}

export interface VisibleRange {
  start: number;
  end: number;
}

/** Slice indices into `total` lines for a `height`-tall viewport at `scroll`. */
export function visibleRange(total: number, height: number, scroll: number): VisibleRange {
  if (total <= 0 || height <= 0) return { start: 0, end: 0 };
  const top = clamp(scroll, 0, maxScroll(total, height));
  return { start: top, end: Math.min(total, top + height) };
}

/** Move the scroll position by `delta` (PgUp=-1, PgDn=+1), clamped. */
export function scrollBy(scroll: number, total: number, height: number, delta: number): number {
  return clamp(scroll + delta, 0, maxScroll(total, height));
}

export function scrollToEnd(total: number, height: number): number {
  return maxScroll(total, height);
}

// ── tool actions (ToolPanel) ────────────────────────
export interface ToolAction {
  id: string;
  title: string;
  done: boolean;
}
