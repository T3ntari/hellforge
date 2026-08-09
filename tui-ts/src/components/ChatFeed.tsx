/** HELL'S CODE TypeScript TUI — streaming chat feed.
 *
 *  Renders `FeedItem`s (streaming chunks from the Python bridge) with
 *  word-wrap, PgUp/PgDn scrollback, and per-line colors from the hellfire
 *  theme (src/theme.ts). While `thinking` is set, an animated indicator is
 *  pinned to the bottom of the viewport.
 *
 *  Layout notes:
 *  - The root Box flexes to fill whatever space the App gives it; the
 *    viewport (width/height) is measured with `measureElement` after layout.
 *  - The message content is an in-flow inner column with an EXPLICIT height
 *    (the measured viewport, or a terminal-derived fallback). A fixed
 *    height means the content can never grow the root and break the
 *    measurement; overflow is clipped by the root's `overflow="hidden"`.
 *    (Previously the inner column was `position="absolute"`, which does not
 *    render in Ink 5.x — the feed was invisible.)
 *  - Scrollback: `scrollTop` is the index of the first visible row. Live
 *    mode follows the newest rows (scrollTop = rows - height); PgUp/PgDn
 *    move by a page and PgDn returns to live. */

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Box, Text, measureElement, useInput, useStdout } from "ink";
import type { DOMElement } from "ink";
import type { Color, FeedItem } from "../protocol.js";
import { tokenHex } from "../theme.js";
import { Markdown } from "../markdown.js";

interface Row {
  text: string;
  color: Color | null;
}

const THINKING_TEXT = "▍thinking";

/** Word-wrap a single item's text into display rows. Newlines are kept as
 *  row breaks; words wider than `width` are hard-split. */
export function wrapText(text: string, width: number): string[] {
  const safeWidth = Math.max(1, width);
  const out: string[] = [];
  for (const seg of text.split("\n")) {
    if (seg === "") {
      out.push("");
      continue;
    }
    const words = seg.split(/\s+/).filter((w) => w !== "");
    if (words.length === 0) {
      out.push("");
      continue;
    }
    let line = "";
    for (const word of words) {
      if (line === "") {
        line = word;
      } else if (line.length + 1 + word.length <= safeWidth) {
        line += ` ${word}`;
      } else {
        out.push(line);
        line = word;
      }
      while (line.length > safeWidth) {
        out.push(line.slice(0, safeWidth));
        line = line.slice(safeWidth);
      }
    }
    out.push(line);
  }
  return out;
}

export interface ChatFeedProps {
  items: FeedItem[];
  thinking: boolean;
}

export default function ChatFeed({ items, thinking }: ChatFeedProps) {
  const { stdout } = useStdout();
  const outerRef = useRef<DOMElement | null>(null);
  const [viewport, setViewport] = useState<{ width: number; height: number } | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [tick, setTick] = useState(0);
  const atBottomRef = useRef(true);

  // Measure the flex-allocated viewport after every layout pass. The
  // state update bails out when the size is unchanged, so no render loop.
  useLayoutEffect(() => {
    const el = outerRef.current;
    if (!el) {
      return;
    }
    try {
      const m = measureElement(el);
      setViewport((prev) =>
        prev && prev.width === m.width && prev.height === m.height ? prev : m,
      );
    } catch {
      // Not laid out yet — retry on the next render.
    }
  });

  // Animated thinking indicator while the backend is working.
  useEffect(() => {
    if (!thinking) {
      setTick(0);
      return;
    }
    const id = setInterval(() => setTick((t) => t + 1), 250);
    return () => clearInterval(id);
  }, [thinking]);

  const fallbackHeight = Math.max(1, (stdout.rows ?? 24) - 4);
  const fallbackWidth = Math.max(10, (stdout.columns ?? 80) - 2);
  const height = viewport !== null && viewport.height >= 1 ? viewport.height : fallbackHeight;
  const width = viewport !== null && viewport.width >= 10 ? viewport.width : fallbackWidth;
  const contentWidth = Math.max(1, width - 2);
  const innerWidth = Math.max(1, width - 2);

  // ── rows ──
  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    if (items.length === 0) {
      out.push({ text: "— awaiting first message —", color: "dim" });
    }
    for (const item of items) {
      const wrapped = wrapText(item.text, contentWidth);
      wrapped.forEach((line, i) => {
        out.push({ text: i === 0 ? line : `  ${line}`, color: item.color });
      });
    }
    return out;
  }, [items, contentWidth]);

  const maxScroll = Math.max(0, rows.length - height);

  // Follow the newest rows while live; stay put (clamped) when scrolled back.
  useLayoutEffect(() => {
    setScrollTop((prev) => {
      const max = Math.max(0, rows.length - height);
      if (atBottomRef.current) {
        return max;
      }
      return Math.min(prev, max);
    });
  }, [rows.length, height]);

  // ── scrollback: PgUp / PgDn ──
  const page = Math.max(1, height - 1);
  useInput((_input, key) => {
    if (key.pageUp) {
      atBottomRef.current = false;
      setScrollTop((prev) => Math.min(prev + page, maxScroll));
    } else if (key.pageDown) {
      setScrollTop((prev) => {
        const next = Math.max(0, prev - page);
        if (next <= maxScroll) {
          atBottomRef.current = true;
          return maxScroll;
        }
        return next;
      });
    }
  });

  const slice = rows.slice(scrollTop, scrollTop + height);

  return (
    <Box flexGrow={1} overflow="hidden" ref={outerRef}>
      <Box flexDirection="column" width={innerWidth} height={height}>
        {slice.map((row, i) => (
          row.color === null ? (
            <Markdown key={i} text={row.text} />
          ) : (
            <Text key={i} color={tokenHex(row.color)}>
              {row.text}
            </Text>
          )
        ))}
        {thinking && (
          <Text color={tokenHex("dim")}>{`${THINKING_TEXT}${".".repeat((tick % 3) + 1)}`}</Text>
        )}
      </Box>
    </Box>
  );
}
