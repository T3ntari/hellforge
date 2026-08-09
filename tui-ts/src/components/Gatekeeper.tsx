import React from "react";
import { Box, Text, useInput } from "ink";
import type { AskState, Color } from "../protocol.js";

const TOKEN_HEX: Record<Color, string> = {
  accent: "#ff4d4d",
  accent2: "#ff8c42",
  text: "#ffebdc",
  dim: "#8c827d",
  ok: "#96c88c",
  err: "#ff6446",
  warn: "#f0be5a",
};

const CHOICE_LABEL: Record<"y" | "n" | "e", { label: string; color: Color }> = {
  y: { label: "[Y]es", color: "ok" },
  n: { label: "[N]o", color: "err" },
  e: { label: "[E]dit block", color: "accent2" },
};

export interface GatekeeperProps {
  ask: AskState | null;
  onAnswer: (value: "y" | "n" | "e") => void;
}

export function Gatekeeper({ ask, onAnswer }: GatekeeperProps) {
  useInput(
    (input) => {
      if (!ask) return;
      const key = input.toLowerCase();
      if (key === "y") {
        onAnswer("y");
      } else if (key === "n") {
        onAnswer("n");
      } else if (key === "e" && ask.choices.includes("e")) {
        onAnswer("e");
      }
    },
    { isActive: ask !== null },
  );

  if (!ask) return null;

  const order: Array<"y" | "n" | "e"> = ["y", "n", "e"];
  return (
    <Box flexDirection="column" alignItems="center" marginTop={1}>
      <Box
        borderStyle="round"
        borderColor={TOKEN_HEX.accent2}
        flexDirection="column"
        paddingX={2}
        paddingY={1}
        width={76}
      >
        <Box flexDirection="column">
          <Text bold color={TOKEN_HEX.text}>{ask.question}</Text>
          {ask.detail ? <Text color={TOKEN_HEX.dim}>{ask.detail}</Text> : null}
        </Box>
        <Box marginTop={1} flexDirection="row">
          {order.map((choice, i) => {
            const enabled = ask.choices.includes(choice);
            const c = CHOICE_LABEL[choice];
            return (
              <React.Fragment key={choice}>
                {i > 0 ? <Text color={TOKEN_HEX.dim}> / </Text> : null}
                <Text color={enabled ? TOKEN_HEX[c.color] : TOKEN_HEX.dim}>
                  {enabled ? c.label : `[${choice.toUpperCase()}]`}
                </Text>
              </React.Fragment>
            );
          })}
        </Box>
      </Box>
    </Box>
  );
}
