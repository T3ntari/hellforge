import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";
import type { BootCheck } from "../boot.js";

export interface SplashProps {
  status?: string;
  version?: string;
  checks?: BootCheck[];
}

// 5x5 block-letter font (one row per line of the banner).
const FONT: Record<string, readonly string[]> = {
  H: ["H   H", "H   H", "HHHHH", "H   H", "H   H"],
  E: ["EEEEE", "E    ", "EEEE ", "E    ", "EEEEE"],
  L: ["L    ", "L    ", "L    ", "L    ", "LLLLL"],
  "'": [" '", "' ", "  ", "  ", "  "],
  S: [" SSS ", "S    ", " SSS ", "    S", "SSSS "],
  C: [" CCCC", "C    ", "C    ", "C    ", " CCCC"],
  O: [" OOOO", "O   O", "O   O", "O   O", " OOOO"],
  D: ["DDDD ", "D   D", "D   D", "D   D", "DDDD "],
  " ": ["   ", "   ", "   ", "   ", "   "],
};

function blockBanner(text: string): string[] {
  const rows = ["", "", "", "", ""];
  let first = true;
  for (const ch of text.toUpperCase()) {
    const glyph = FONT[ch] ?? FONT[" "];
    for (let r = 0; r < 5; r++) {
      rows[r] += (first ? "" : " ") + glyph[r];
    }
    first = false;
  }
  return rows;
}

const CHECK_MARK: Record<BootCheck["state"], { mark: string; color: string }> = {
  ok: { mark: "\u2713", color: tokenHex("ok") },
  fail: { mark: "\u2717", color: tokenHex("err") },
  pending: { mark: "\u2026", color: tokenHex("dim") },
};

/** Boot screen: block-text banner, version line, and the setup checklist
 *  (python / bridge / model / ollama) rendered as ✓/✗ items before the app
 *  enters the main loop. */
export default function Splash({
  status = "starting agent bridge...",
  version,
  checks,
}: SplashProps): React.ReactElement {
  const banner = blockBanner("HELL'S CODE");
  return (
    <Box flexDirection="column" alignItems="center" justifyContent="center" height="100%">
      {banner.map((row, i) => (
        <Text key={i} bold color={tokenHex("accent")}>
          {row}
        </Text>
      ))}
      <Box>
        <Text color={tokenHex("accent2")}>{status}</Text>
        {version ? <Text color={tokenHex("dim")}>  {version}</Text> : null}
      </Box>
      {checks && checks.length > 0 ? (
        <Box flexDirection="column" marginTop={1}>
          {checks.map((c) => {
            const m = CHECK_MARK[c.state];
            return (
              <Box key={c.id}>
                <Text color={m.color}>{m.mark} </Text>
                <Text color={tokenHex("text")}>{c.label}</Text>
                {c.detail ? <Text color={tokenHex("dim")}>  {c.detail}</Text> : null}
              </Box>
            );
          })}
        </Box>
      ) : null}
      <Text color={tokenHex("dim")}>- T3ntari</Text>
    </Box>
  );
}
