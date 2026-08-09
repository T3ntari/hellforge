import React from "react";
import { Text } from "ink";
import { TOKENS } from "./frame.js";

/** Lightweight markdown renderer for the chat feed: fenced code blocks
 *  with a language tag + keyword tinting, bold/italic, inline code,
 *  headers, lists, blockquotes. Plain and dependency-free. */

const KEYWORDS = new Set([
  "def", "class", "import", "from", "return", "if", "else", "elif", "for",
  "while", "in", "not", "and", "or", "None", "True", "False", "async",
  "await", "with", "try", "except", "lambda", "yield", "pass", "break",
  "continue", "T", "N", "D", "V", "@bpm", "@key", "@vel", "@dur", "play",
  "note", "chord", "pedal", "rest", "print", "assert", "include", "prog",
  "perc", "for", "repeat",
]);

function CodeLine({ line }: { line: string }) {
  // Tiny token tinting: keywords in accent2, strings in sage-ish, rest dim.
  const tokens: Array<{ t: string; c?: string }> = [];
  const re = /(\"[^\"]*\"|'[^']*'|[A-Za-z_@][A-Za-z0-9_@]*|\d+)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) tokens.push({ t: line.slice(last, m.index) });
    const tok = m[0];
    let c: string | undefined;
    if (tok.startsWith("\"") || tok.startsWith("'")) c = TOKENS.ok;
    else if (KEYWORDS.has(tok)) c = TOKENS.accent2;
    else if (/^\d+$/.test(tok)) c = TOKENS.warn;
    tokens.push({ t: tok, c });
    last = m.index + tok.length;
  }
  if (last < line.length) tokens.push({ t: line.slice(last) });
  return (
    <Text color={TOKENS.dim}>
      {tokens.map((tok, i) => (
        <Text key={i} color={tok.c}>
          {tok.t}
        </Text>
      ))}
    </Text>
  );
}

function CodeBlock({ lang, lines }: { lang: string; lines: string[] }) {
  return (
    <Text>
      <Text color={TOKENS.accent2} bold>
        {lang ? ` ─ ${lang} ─` : " ─ code ─"}
      </Text>
      {"\n"}
      {lines.map((l, i) => (
        <CodeLine key={i} line={l} />
      ))}
    </Text>
  );
}

function InlineText({ text }: { text: string }) {
  // **bold**  *italic*  `code`
  const parts: React.ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      parts.push(<Text key={k++} bold color={TOKENS.text}>{tok.slice(2, -2)}</Text>);
    } else if (tok.startsWith("`")) {
      parts.push(<Text key={k++} color={TOKENS.accent2}>{tok.slice(1, -1)}</Text>);
    } else if (tok.startsWith("*")) {
      parts.push(<Text key={k++} italic color={TOKENS.text}>{tok.slice(1, -1)}</Text>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <Text>{parts}</Text>;
}

/** Render a full markdown-ish string as Ink nodes. */
export function Markdown({ text }: { text: string }) {
  const lines = (text || "").split("\n");
  const out: React.ReactNode[] = [];
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const line = lines[i];
    const fence = /^```(\w*)\s*$/.exec(line);
    if (fence) {
      const lang = fence[1];
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !/^```/.test(lines[i])) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1; // skip closing fence
      out.push(<CodeBlock key={key++} lang={lang} lines={code} />);
      continue;
    }
    if (/^#{1,4}\s/.test(line)) {
      const level = line.match(/^#+/)?.[0].length ?? 1;
      out.push(
        <Text key={key++} bold color={level <= 2 ? TOKENS.accent : TOKENS.text}>
          {line.replace(/^#+\s*/, "")}
        </Text>,
      );
      i += 1;
      continue;
    }
    if (/^\s*[-*]\s+/.test(line)) {
      out.push(
        <Text key={key++}>
          <Text color={TOKENS.accent}>• </Text>
          <InlineText text={line.replace(/^\s*[-*]\s+/, "")} />
        </Text>,
      );
      i += 1;
      continue;
    }
    if (/^\s*>\s?/.test(line)) {
      out.push(
        <Text key={key++} color={TOKENS.dim} italic>
          {line.replace(/^\s*>\s?/, "")}
        </Text>,
      );
      i += 1;
      continue;
    }
    out.push(<InlineText key={key++} text={line} />);
    i += 1;
  }
  return <>{out}</>;
}
