import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";

export interface HeaderProps {
  model?: string;
}

/** 'HELL'S CODE' red banner + '- T3ntari' dim grey, mirroring the Python
 *  curses TUI header. */
export default function Header({ model }: HeaderProps): React.ReactElement {
  return (
    <Box flexDirection="column">
      <Box>
        <Text bold color={tokenHex("accent")}>HELL&apos;S CODE</Text>
        <Text color={tokenHex("dim")}>  - T3ntari</Text>
        {model !== undefined ? (
          <Text color={tokenHex("dim")}>  ·  {model}</Text>
        ) : null}
      </Box>
      <Box
        borderStyle="single"
        borderTop
        borderBottom={false}
        borderLeft={false}
        borderRight={false}
        borderColor={tokenHex("border")}
      />
    </Box>
  );
}
