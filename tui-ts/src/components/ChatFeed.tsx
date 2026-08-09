/** PLACEHOLDER — owned by tickets-ts-feed (ChatFeed.tsx). Replace wholesale.
 *  Contract:
 *    { items: FeedItem[]; thinking: boolean;
 *      onSubmit: (line: string) => void; onOpenPalette: () => void }
 *  Word-wrap + PgUp/PgDn scrollback via ../frame.js (wrap, visibleRange,
 *  scrollBy, scrollToEnd); raw-key input via ../input.ts; type "/" at input
 *  start -> onOpenPalette(); Enter (non-empty) -> onSubmit(line). */
import { Box, Text } from "ink";
import type { FeedItem } from "../protocol.js";

export interface ChatFeedProps {
  items: FeedItem[];
  thinking: boolean;
  onSubmit: (line: string) => void;
  onOpenPalette: () => void;
}

export default function ChatFeed(props: ChatFeedProps): JSX.Element {
  return (
    <Box flexDirection="column" flexGrow={1}>
      {props.items.map((item, i) => (
        <Text key={i}>{item.text}</Text>
      ))}
      {props.thinking ? <Text color="gray">…</Text> : null}
      <Text color="gray">&gt; </Text>
    </Box>
  );
}
