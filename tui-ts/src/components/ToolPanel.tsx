import React from "react";
import { Box, Text } from "ink";
import { TOKENS } from "../frame.js";

export interface ToolAction {
  title: string;
  status: "running" | "done" | "error";
  summary?: string;
}

interface ToolPanelProps {
  actions: ToolAction[];
}

/** Spinner line that collapses into a ✓ accordion of past actions. */
export default function ToolPanel({ actions }: ToolPanelProps) {
  if (actions.length === 0) return null;
  return (
    <Box flexDirection="column">
      {actions.map((a, i) => {
        if (a.status === "running") {
          return (
            <Text key={i} color={TOKENS.accent2} dimColor>
              {"\u25cf "}
              {a.title}
              {"..."}
            </Text>
          );
        }
        return (
          <Text key={i} color={a.status === "done" ? TOKENS.ok : TOKENS.err} dimColor>
            {a.status === "done" ? "\u2713 " : "\u2717 "}
            {a.title}
            {a.summary ? ` ${a.summary}` : ""}
          </Text>
        );
      })}
    </Box>
  );
}
