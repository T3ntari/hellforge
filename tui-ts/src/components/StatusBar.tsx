/** PLACEHOLDER — owned by tickets-ts-chrome (StatusBar.tsx). Replace wholesale.
 *  Contract: { model?: string; mode?: string; context?: number; status?: string }
 *  model/mode/context% left, status (dim) right — mirrors Python tui.py. */
import { Box, Text } from "ink";

export interface StatusBarProps {
  model?: string;
  mode?: string;
  context?: number;
  status?: string;
}

export default function StatusBar(_props: StatusBarProps): JSX.Element {
  return (
    <Box>
      <Text color="gray">StatusBar</Text>
    </Box>
  );
}
