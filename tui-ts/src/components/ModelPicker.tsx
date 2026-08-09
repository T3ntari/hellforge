/** PLACEHOLDER — owned by tickets-ts-gate (ModelPicker.tsx). Replace wholesale.
 *  Contract: { open: boolean; onClose: () => void; onPick: (provider, model) => void }.
 *  Arrow-selectable provider/model menu. NOTE: the stdio protocol has no
 *  model-change message yet — App currently just closes the picker on pick
 *  (see App.tsx handleModelPick); wire a submit/answer channel here when the
 *  bridge grows one. */
import { Box, Text } from "ink";

export interface ModelPickerProps {
  open: boolean;
  onClose: () => void;
  onPick: (provider: string, model: string) => void;
}

export default function ModelPicker(_props: ModelPickerProps): JSX.Element {
  return (
    <Box>
      <Text color="gray">ModelPicker</Text>
    </Box>
  );
}
