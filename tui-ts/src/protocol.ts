/** Shared protocol between the TypeScript TUI and the Python agent backend.
 *  JSON-lines over stdio: the TS side spawns `python run.py ai bridge` and
 *  exchanges these messages. */
export interface PyToTs {
  type: "system" | "chunk" | "feed" | "thinking" | "box" | "boxline"
       | "ask" | "status" | "mode" | "done" | "error";
  text?: string;
  color?: string;
  on?: boolean;
  title?: string;
  key?: string;
  question?: string;
  detail?: string;
  choices?: Array<"y" | "n" | "e">;
}

export interface TsToPy {
  type: "submit" | "answer" | "quit";
  line?: string;
  key?: string;
  value?: "y" | "n" | "e";
}

export type Color = "accent" | "accent2" | "text" | "dim" | "ok" | "err" | "warn";

export interface FeedItem { color: Color | null; text: string; }

export interface AskState {
  key: string;
  question: string;
  detail: string;
  choices: Array<"y" | "n" | "e">;
}
