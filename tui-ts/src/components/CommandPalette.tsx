/** PLACEHOLDER — owned by tickets-ts-palette (CommandPalette.tsx). Replace
 *  wholesale. Contract: { open: boolean; onClose: () => void; onPick: (command: string) => void }.
 *  Arrow-selectable dropdown of 16 commands (/fix /edit /search /test /upload
 *  /model /mode /memory /todo /ticket /config /cost /review /undo /help /exit);
 *  Enter picks -> onPick(cmd), Esc -> onClose(). */
import { Box, Text } from "ink";

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onPick: (command: string) => void;
}

export default function CommandPalette(_props: CommandPaletteProps): JSX.Element {
  return (
    <Box>
      <Text color="gray">CommandPalette</Text>
    </Box>
  );
}
