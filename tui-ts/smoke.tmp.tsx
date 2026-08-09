import React, { useState } from "react";
import { render, Text, Box, useInput } from "ink";
import { CommandPalette } from "/mnt/data/E/piano-dsl-wt-palette/tui-ts/src/components/CommandPalette";
import { Complete } from "/mnt/data/E/piano-dsl-wt-palette/tui-ts/src/components/Complete";

let seed = "$pa";
const Dummy = () => {
  const [input, setInput] = useState(seed);
  const [picked, setPicked] = useState("");
  const [open, setOpen] = useState(true);
  return (
    <Box flexDirection="column">
      <CommandPalette open={open} onPick={(c) => { setPicked(c); setOpen(false); }} onClose={() => setOpen(false)} />
      <Complete input={input} onComplete={setInput} />
      <Text>input={input} picked={picked || "(none)"} open={String(open)}</Text>
    </Box>
  );
};
const app = render(<Dummy />, { exitOnCtrlC: false });
setTimeout(() => app.unmount(), 10000);
