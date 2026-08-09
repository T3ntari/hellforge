/** PLACEHOLDER — owned by tickets-ts-gate (Gatekeeper.tsx). Replace wholesale.
 *  Contract: { ask: AskState; onAnswer: (key, value) => void }.
 *  Blocking modal — question, detail, [Y]es/[N]o/[E]dit; keys resolve via
 *  bridge.answer() (App passes it as onAnswer and clears the ask state). */
import { Box, Text } from "ink";
import type { AskState } from "../protocol.js";

export interface GatekeeperProps {
  ask: AskState;
  onAnswer: (key: string, value: "y" | "n" | "e") => void;
}

export default function Gatekeeper(props: GatekeeperProps): JSX.Element {
  return (
    <Box flexDirection="column">
      <Text color="yellow">Gatekeeper: {props.ask.question}</Text>
      <Text color="gray">[Y]es [N]o [E]dit</Text>
    </Box>
  );
}
