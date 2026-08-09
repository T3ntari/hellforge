/** PLACEHOLDER — owned by tickets-ts-tools (ToolPanel.tsx). Replace wholesale.
 *  Contract: { actions: ToolAction[] } (ToolAction from ../frame.js).
 *  Spinner line while the newest action is !done; past actions collapse to a
 *  ✓ accordion (dim). */
import { Box, Text } from "ink";
import type { ToolAction } from "../frame.js";

export interface ToolPanelProps {
  actions: ToolAction[];
}

export default function ToolPanel(props: ToolPanelProps): JSX.Element {
  return (
    <Box flexDirection="column">
      {props.actions.map((a) => (
        <Text key={a.id} color={a.done ? "gray" : "yellow"}>
          {a.done ? "✓ " : "… "}
          {a.title}
        </Text>
      ))}
    </Box>
  );
}
