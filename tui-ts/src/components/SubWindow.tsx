/** PLACEHOLDER — owned by tickets-ts-tools (SubWindow.tsx). Replace wholesale.
 *  Contract: { title: string; lines: string[] }. Bordered box rendering
 *  boxline events live; App unmounts it when the box closes. */
import { Box, Text } from "ink";

export interface SubWindowProps {
  title: string;
  lines: string[];
}

export default function SubWindow(props: SubWindowProps): JSX.Element {
  return (
    <Box flexDirection="column">
      <Text color="gray">SubWindow: {props.title}</Text>
      {props.lines.map((l, i) => (
        <Text key={i}>{l}</Text>
      ))}
    </Box>
  );
}
