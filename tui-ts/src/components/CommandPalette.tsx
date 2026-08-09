/** Command palette — arrow-selectable dropdown of the 16 slash commands.
 *  The parent shows it (`open`) while the input line starts with "/";
 *  Enter reports the picked command via `onPick`, Esc closes via the
 *  optional `onClose`. While open, this component owns ↑/↓/Enter/Esc —
 *  the parent must ignore its own input handlers for those keys.
 *  Theme tokens (Color from protocol.ts) resolve to the HELLFORGE Claude
 *  palette here; App.tsx may reuse COLOR_HEX. */
import { useEffect, useState } from "react";
import { Box, Text, useInput } from "ink";
import type { Color } from "../protocol";

/** Theme tokens → 24-bit palette (matches plugins/llm/theme.py). */
export const COLOR_HEX: Record<Color, string> = {
  accent: "#c4a3f6", // violet
  accent2: "#d8c4fa", // light violet (borders / headers)
  text: "#f7f3ea", // cream
  dim: "#8c8478", // muted
  ok: "#96b48c", // sage
  err: "#cd785a", // terracotta
  warn: "#e0b46e", // amber
};

export interface PaletteCommand {
  cmd: string;
  hint: string;
}

/** The 16 slash commands, in canonical order (matches the Python TUI). */
export const PALETTE_COMMANDS: readonly PaletteCommand[] = [
  { cmd: "/fix", hint: "<task>       agentic multi-step task" },
  { cmd: "/edit", hint: "<file>      targeted line-range edits" },
  { cmd: "/search", hint: "<query>    codebase search (~ for similar)" },
  { cmd: "/test", hint: "[file]      run the test suite" },
  { cmd: "/upload", hint: "<path>     attach a file" },
  { cmd: "/model", hint: "            model picker" },
  { cmd: "/mode", hint: "plan|auto|ask" },
  { cmd: "/memory", hint: "           long-form memory" },
  { cmd: "/todo", hint: "             checklist" },
  { cmd: "/ticket", hint: "           tickets for other bots" },
  { cmd: "/config", hint: "           settings" },
  { cmd: "/cost", hint: "             session cost" },
  { cmd: "/review", hint: "           review working-tree diff" },
  { cmd: "/undo", hint: "[N]         revert applied turns" },
  { cmd: "/help", hint: "             command list" },
  { cmd: "/exit", hint: "             leave the session" },
];

export interface CommandPaletteProps {
  /** Whether the palette is shown; selection resets whenever it turns true. */
  open: boolean;
  /** Called with the raw command (e.g. "/fix") when Enter is pressed. */
  onPick: (cmd: string) => void;
  /** Called when Esc is pressed; the parent should flip `open` to false. */
  onClose?: () => void;
  /** Called with a printable character typed while open — the parent
   *  closes the palette and continues editing (e.g. typing "e" after "/"
   *  keeps "/e" going toward "/exit"). */
  onType?: (char: string) => void;
}

export function CommandPalette({ open, onPick, onClose, onType }: CommandPaletteProps) {
  const [selected, setSelected] = useState(0);
  const count = PALETTE_COMMANDS.length;

  useEffect(() => {
    if (open) setSelected(0);
  }, [open]);

  useInput(
    (input, key) => {
      if (key.upArrow) {
        setSelected((i) => (i - 1 + count) % count);
      } else if (key.downArrow) {
        setSelected((i) => (i + 1) % count);
      } else if (key.return) {
        onPick(PALETTE_COMMANDS[selected].cmd);
      } else if (key.escape) {
        onClose?.();
      } else if (input && input.length === 1 && !key.ctrl && !key.meta) {
        onType?.(input);
      }
    },
    { isActive: open },
  );

  if (!open) return null;

  return (
    <Box flexDirection="column" borderStyle="round" borderColor={COLOR_HEX.accent2} paddingX={1}>
      <Text color={COLOR_HEX.dim}>commands — ↑/↓ move, Enter pick, Esc close</Text>
      {PALETTE_COMMANDS.map((item, i) => {
        const active = i === selected;
        return (
          <Box key={item.cmd}>
            <Text color={active ? COLOR_HEX.accent : COLOR_HEX.dim}>
              {active ? "❯ " : "  "}
            </Text>
            <Text color={active ? COLOR_HEX.text : COLOR_HEX.dim} bold={active}>
              {item.cmd}
            </Text>
            <Text color={COLOR_HEX.dim}> {item.hint}</Text>
          </Box>
        );
      })}
    </Box>
  );
}
