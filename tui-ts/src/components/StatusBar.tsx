import React from "react";
import { Box, Text } from "ink";
import { tokenHex } from "../theme.js";

export interface StatusBarProps {
  model: string;
  mode: string;
  context?: number;
  status?: string;
  branch?: string;
  files?: string[];
  tokens?: number;
}

const CONTEXT_WARN = 80;

function contextColor(pct: number): string {
  if (pct >= CONTEXT_WARN) return tokenHex("warn");
  return tokenHex("ok");
}

/** Workspace status bar (top, under the banner): model / mode / active git
 *  branch / estimated session tokens / current file targets on the left;
 *  the bridge `status` text (or context %) on the right. Subtle tints only. */
export default function StatusBar({
  model,
  mode,
  context = 0,
  status = "",
  branch,
  files,
  tokens,
}: StatusBarProps): React.ReactElement {
  const pct = Math.max(0, Math.min(100, Math.round(context)));
  const shownFiles = (files ?? []).slice(0, 3).join(", ");
  const meta: string[] = [];
  if (branch) meta.push(`\u273f ${branch}`);
  if (typeof tokens === "number" && tokens > 0) meta.push(`~\u2248${tokens} tok`);
  const metaText = meta.join("  ");
  return (
    <Box justifyContent="space-between" width="100%">
      <Box>
        <Text color={tokenHex("accent2")}>{model}</Text>
        <Text color={tokenHex("dim")}>  |  </Text>
        <Text color={tokenHex("text")}>{mode}</Text>
        {metaText ? <Text color={tokenHex("dim")}>  {metaText}</Text> : null}
        {shownFiles ? (
          <Text color={tokenHex("text")}>
            {"  "}
            <Text color={tokenHex("dim")}>files:</Text> {shownFiles}
          </Text>
        ) : null}
      </Box>
      {status ? (
        <Text color={tokenHex("dim")}>{status}</Text>
      ) : (
        <Text color={contextColor(pct)}>context {pct}%</Text>
      )}
    </Box>
  );
}
