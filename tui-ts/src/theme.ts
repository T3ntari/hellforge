/** HELLFORGE TUI theme — hellfire palette tokens, ANSI builders and the
 *  Color -> ANSI X3.64 SGR mapping used by the feed.
 *
 *  The RGB tokens mirror the Python curses TUI (plugins/llm/tui.py HELLFIRE)
 *  so both UIs render the same look. The Color names are the ones the
 *  bridge sends (see protocol.ts). */

import type { Color } from "./protocol.js";

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

export const HELLFIRE = {
  accent: { r: 255, g: 77, b: 77 }, // fiery red — primary accent
  accent2: { r: 255, g: 140, b: 66 }, // ember orange
  text: { r: 255, g: 235, b: 220 }, // warm off-white
  dim: { r: 140, g: 130, b: 125 }, // grey (the "- T3ntari" line)
  ok: { r: 150, g: 200, b: 140 }, // sage
  err: { r: 255, g: 100, b: 70 }, // hot error
  warn: { r: 240, g: 190, b: 90 }, // amber
  border: { r: 120, g: 40, b: 40 }, // dark ember border
} as const;

export type ThemeToken = keyof typeof HELLFIRE;

export function rgbToHex({ r, g, b }: Rgb): string {
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1).toUpperCase()}`;
}

export function tokenHex(name: ThemeToken): string {
  return rgbToHex(HELLFIRE[name]);
}

/** Color -> ANSI X3.64 SGR foreground code. Used by the raw feed layer;
 *  Ink components should use tokenHex() instead. */
export const ANSI_X3: Record<ThemeToken, number> = {
  accent: 91, // bright red
  accent2: 33, // yellow (closest basic warm hue to ember orange)
  text: 37, // white
  dim: 90, // bright black (dark grey)
  ok: 32, // green
  err: 91, // bright red
  warn: 93, // bright yellow
  border: 31, // red
};

export function ansiCode(name: ThemeToken): number {
  return ANSI_X3[name];
}

export const ESC = "\u001b[";
export const RESET = `${ESC}0m`;

/** Wrap text in ANSI SGR escapes for the given token (unstyled passthrough
 *  for anything not in the palette). */
export function paint(name: ThemeToken, text: string): string {
  return `${ESC}${ansiCode(name)}m${text}${RESET}`;
}

export function boldPaint(name: ThemeToken, text: string): string {
  return `${ESC}1;${ansiCode(name)}m${text}${RESET}`;
}

export function dimPaint(text: string): string {
  return `${ESC}2m${text}${RESET}`;
}

/** Strip ANSI SGR sequences (e.g. to compute true display width). */
export function stripAnsi(text: string): string {
  return text.replace(/\u001b\[[0-9;]*m/g, "");
}

/** Resolve a protocol Color (or null) to a paint function. */
export function paintColor(color: Color | null, text: string): string {
  return color === null ? text : paint(color, text);
}
