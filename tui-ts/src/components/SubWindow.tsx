import React from "react";
import { Box, Text } from "ink";
import { TOKENS } from "../frame.js";

interface SubWindowProps {
  title: string;
  lines: string[];
}

/** Bordered box for live command output — never clutters the main feed. */
export default function SubWindow({ title, lines }: SubWindowProps) {
  const width = 80;
  const top = "\u250c" + "\u2500".repeat(width - 2) + "\u2510";
  const bottom = "\u2514" + "\u2500".repeat(width - 2) + "\u2518";
  return (
    <Box flexDirection="column" marginY={1} marginX={2}>
      <Text color={TOKENS.accent2} bold>
        {top}
      </Text>
      <Text color={TOKENS.accent2} bold>
        {"\u2502"} {title}
      </Text>
      {lines.slice(-12).map((l, i) => (
        <Text key={i} color={TOKENS.dim}>
          {"\u2502"} {l.slice(0, width - 4)}
        </Text>
      ))}
      <Text color={TOKENS.accent2} bold>
        {bottom}
      </Text>
    </Box>
  );
}
