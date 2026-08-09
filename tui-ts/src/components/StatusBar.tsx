import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";

export interface StatusBarProps {
  model: string;
  mode: string;
  context: number;
}

const CONTEXT_WARN = 80;

function contextColor(pct: number): string {
  if (pct >= CONTEXT_WARN) return tokenHex("warn");
  return tokenHex("ok");
}

/** Model / mode / context% bar. `context` is a 0..100 percent (the bridge
 *  sends it already scaled); it is clamped defensively. */
export default function StatusBar({ model, mode, context }: StatusBarProps): React.ReactElement {
  const pct = Math.max(0, Math.min(100, Math.round(context)));
  return (
    <Box justifyContent="space-between" width="100%">
      <Box>
        <Text color={tokenHex("accent2")}>{model}</Text>
        <Text color={tokenHex("dim")}>  |  </Text>
        <Text color={tokenHex("text")}>{mode}</Text>
      </Box>
      <Text color={contextColor(pct)}>context {pct}%</Text>
    </Box>
  );
}
