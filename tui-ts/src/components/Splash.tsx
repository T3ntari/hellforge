import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";

export interface SplashProps {
  status?: string;
}

/** Boot screen shown while the agent bridge spawns. */
export default function Splash({ status = "starting agent bridge..." }: SplashProps): React.ReactElement {
  return (
    <Box flexDirection="column" alignItems="center" justifyContent="center" height="100%">
      <Text bold color={tokenHex("accent")}>HELL&apos;S CODE</Text>
      <Text color={tokenHex("accent2")}>{status}</Text>
      <Text color={tokenHex("dim")}>- T3ntari</Text>
    </Box>
  );
}
