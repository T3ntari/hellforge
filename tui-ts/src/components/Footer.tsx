import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";

export const FOOTER_SHORTCUTS: ReadonlyArray<readonly [string, string]> = [
  ["Ctrl+C", "Copy"],
  ["Ctrl+V", "Paste"],
  ["Ctrl+X", "Cut"],
  ["PgUp/PgDn", "scroll"],
  ["Tab", "complete"],
  ["/", "palette"],
  ["/exit", "Leave"],
];

/** Shortcut bar — key names in accent, labels dim. */
export default function Footer(): React.ReactElement {
  return (
    <Box>
      {FOOTER_SHORTCUTS.map(([key, label], i) => (
        <React.Fragment key={key}>
          {i > 0 ? <Text color={tokenHex("dim")}> | </Text> : null}
          <Text color={tokenHex("accent")}>{key}</Text>
          <Text color={tokenHex("dim")}>: {label}</Text>
        </React.Fragment>
      ))}
    </Box>
  );
}
