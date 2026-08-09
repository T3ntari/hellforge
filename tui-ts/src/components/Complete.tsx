/** Tab path completion for /$ uploads. While the input line starts with
 *  "/$", Tab replaces the trailing partial path with the next matching
 *  entry under cwd (scanned with node:fs); repeated Tabs cycle through
 *  the candidates. Directory candidates get a trailing "/" so Tab can
 *  descend. A dim hint row lists the current candidates.
 *  All other input is ignored — the parent keeps its own Tab handling. */
import { useRef } from "react";
import { Box, Text, useInput } from "ink";
import { readdirSync } from "node:fs";
import { join } from "node:path";
import { COLOR_HEX } from "./CommandPalette";

const MAX_MATCHES = 20;
const HINT_ROWS = 6;

export interface Candidates {
  /** Directory prefix as typed, "" for cwd. */
  dir: string;
  /** Partial entry name being completed ("" when completing the dir). */
  partial: string;
  /** Candidate entry names (dirs end with "/"), sorted, capped. */
  matches: string[];
}

/** Scan `base` (everything after "/$") for matching entries in cwd.
 *  Hidden entries (leading ".") are skipped. Returns [] when the
 *  directory does not exist or cannot be read. */
export function findCandidates(base: string): Candidates {
  const slash = base.lastIndexOf("/");
  const dir = slash >= 0 ? base.slice(0, slash) : "";
  const partial = slash >= 0 ? base.slice(slash + 1) : base;
  let matches: string[] = [];
  try {
    matches = readdirSync(join(process.cwd(), dir), { withFileTypes: true })
      .filter((e) => !e.name.startsWith(".") && e.name.startsWith(partial))
      .map((e) => (e.isDirectory() ? e.name + "/" : e.name))
      .sort();
  } catch {
    matches = [];
  }
  return { dir, partial, matches: matches.slice(0, MAX_MATCHES) };
}

export interface CompleteProps {
  /** The current input line; completion reads the tail after "/$". */
  input: string;
  /** Called with the completed line ("/$" + matched path) on Tab. */
  onComplete: (line: string) => void;
}

export function Complete({ input, onComplete }: CompleteProps) {
  const cycleRef = useRef<{ base: string; idx: number } | null>(null);

  useInput((_input, key) => {
    if (!key.tab || !input.startsWith("/$")) return;
    const base = input.slice(2);
    const { dir, matches } = findCandidates(base);
    if (matches.length === 0) {
      cycleRef.current = null;
      return;
    }
    const cycleKey = dir + "|" + matches.join("\u0001");
    if (cycleRef.current?.base !== cycleKey) {
      cycleRef.current = { base: cycleKey, idx: 0 };
    } else {
      cycleRef.current = {
        base: cycleKey,
        idx: (cycleRef.current.idx + 1) % matches.length,
      };
    }
    const name = matches[cycleRef.current.idx];
    onComplete("/$" + (dir ? dir + "/" : "") + name);
  });

  const candidates = input.startsWith("/$") ? findCandidates(input.slice(2)) : null;
  const matches = candidates?.matches ?? [];

  return (
    <Box flexDirection="column">
      {candidates !== null && matches.length > 0 && (
        <Text color={COLOR_HEX.dim}>
          {"  ↳ " + matches.slice(0, HINT_ROWS).join("  ")}
          {matches.length > HINT_ROWS ? "  …" : ""}
        </Text>
      )}
      {candidates !== null && matches.length === 0 && input.length > 2 && (
        <Text color={COLOR_HEX.warn}>  ↳ no matches</Text>
      )}
    </Box>
  );
}
