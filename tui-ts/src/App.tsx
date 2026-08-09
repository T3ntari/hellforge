/** HELL'S CODE TUI root (Ink). Owned by tickets-ts-engine.
 *  Wires the bridge events into App state and renders the component tree.
 *  Component contracts are documented in each placeholder under
 *  src/components/ — the owning agents replace the placeholders wholesale.
 *
 *  bridge prop (from index.ts, see tickets-ts-bridge): a typed emitter
 *  with `on<Event>(type, handler)` subscriptions per PyToTs type plus
 *  submit()/answer()/quit() senders (see BridgeLike below). */
import { Box, useApp, useInput } from "ink";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import type { AskState, Color, FeedItem, PyToTs } from "./protocol.js";
import { feedReducer, type ToolAction } from "./frame.js";
import ChatFeed from "./components/ChatFeed.js";
import CommandPalette from "./components/CommandPalette.js";
import Footer from "./components/Footer.js";
import Gatekeeper from "./components/Gatekeeper.js";
import Header from "./components/Header.js";
import ModelPicker from "./components/ModelPicker.js";
import Splash from "./components/Splash.js";
import StatusBar from "./components/StatusBar.js";
import SubWindow from "./components/SubWindow.js";
import ToolPanel from "./components/ToolPanel.js";

type MsgOf<E extends PyToTs["type"]> = PyToTs & { type: E };

export interface BridgeLike {
  on<E extends PyToTs["type"]>(event: E, handler: (msg: MsgOf<E>) => void): void;
  submit(line: string): void;
  answer(key: string, value: "y" | "n" | "e"): void;
  quit(): void;
}

export interface AppProps {
  bridge: BridgeLike;
}

interface BoxState {
  title: string;
  lines: string[];
}

const QUIT_COMMANDS = new Set(["/exit", "/quit", "/bye"]);

/** Parse "HELL'S CODE v0.1.13 • provider / model • chat mode" for the status bar. */
function parseModel(system: string): string {
  const m = /\u2022\s*([^/]+?)\s*\/\s*([^\u2022]+?)\s*\u2022/.exec(system);
  return m ? `${m[1].trim()}/${m[2].trim()}` : "?";
}

export default function App({ bridge }: AppProps): JSX.Element {
  const { exit } = useApp();
  const [items, dispatch] = useReducer(feedReducer, [] as FeedItem[]);
  const [thinking, setThinking] = useState(false);
  const [box, setBox] = useState<BoxState | null>(null);
  const [actions, setActions] = useState<ToolAction[]>([]);
  const [ask, setAsk] = useState<AskState | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [status, setStatus] = useState("");
  const [mode, setMode] = useState("chat");
  const [model, setModel] = useState("?");
  const [ready, setReady] = useState(false);
  const boxCounter = useRef(0);

  useEffect(() => {
    bridge.on("system", (m) => {
      const text = m.text ?? "";
      setModel(parseModel(text));
      dispatch({ type: "append", item: { color: "dim", text } });
      setReady(true);
    });
    bridge.on("chunk", (m) => {
      dispatch({ type: "chunk", text: m.text ?? "", color: null });
      setReady(true);
    });
    bridge.on("feed", (m) => {
      dispatch({
        type: "append",
        item: { color: (m.color as Color | null) ?? null, text: m.text ?? "" },
      });
      setReady(true);
    });
    bridge.on("thinking", (m) => setThinking(Boolean(m.on)));
    bridge.on("box", (m) => {
      // protocol.ts lacks the `open` field the Python bridge sends; cast here
      // (ts-bridge/ts-integrate may add it to the shared protocol later).
      const open = (m as unknown as { open?: boolean }).open ?? false;
      if (open) {
        const id = String(++boxCounter.current);
        setBox({ title: m.title ?? "", lines: [] });
        setActions((a) => [...a, { id, title: m.title ?? "", done: false }]);
      } else {
        setBox(null);
        setActions((a) => {
          if (a.length === 0) return a;
          const next = [...a];
          const last = next[next.length - 1];
          if (!last.done) next[next.length - 1] = { ...last, done: true };
          return next;
        });
      }
    });
    bridge.on("boxline", (m) => {
      setBox((b) => (b ? { ...b, lines: [...b.lines, m.text ?? ""] } : b));
    });
    bridge.on("ask", (m) => {
      setAsk({
        key: m.key ?? "",
        question: m.question ?? "",
        detail: m.detail ?? "",
        choices: (m.choices ?? ["y", "n"]) as Array<"y" | "n" | "e">,
      });
    });
    bridge.on("status", (m) => setStatus(m.text ?? ""));
    bridge.on("mode", (m) => setMode(m.text ?? "chat"));
    bridge.on("error", (m) => {
      dispatch({ type: "append", item: { color: "err", text: `[error] ${m.text ?? ""}` } });
      setReady(true);
    });
    bridge.on("done", () => exit());
  }, [bridge, exit]);

  const submit = useCallback(
    (line: string) => {
      if (!line.trim()) return;
      bridge.submit(line);
    },
    [bridge],
  );

  const handleAnswer = useCallback(
    (key: string, value: "y" | "n" | "e") => {
      bridge.answer(key, value);
      setAsk(null);
    },
    [bridge],
  );

  const handlePick = useCallback(
    (command: string) => {
      setPaletteOpen(false);
      if (command === "/model") {
        setPickerOpen(true);
        return;
      }
      if (QUIT_COMMANDS.has(command)) {
        bridge.quit();
        return;
      }
      submit(command);
    },
    [bridge, submit],
  );

  const handleModelPick = useCallback((_provider: string, _model: string) => {
    // The stdio protocol has no model-change message yet — the picker is a
    // local UI for now. Wire a submit/answer channel here when the bridge
    // grows one (see ModelPicker placeholder note).
    setPickerOpen(false);
  }, []);

  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      // Ink intercepts Ctrl+C by default (exitOnCtrlC) — this branch only
      // runs if index.ts renders with exitOnCtrlC: false.
      bridge.quit();
      setTimeout(() => process.exit(0), 1500);
      return;
    }
    if (ask || !key.escape) return;
    if (pickerOpen) {
      setPickerOpen(false);
      return;
    }
    if (!paletteOpen) setPaletteOpen(true);
  });

  return (
    <Box flexDirection="column" height="100%">
      {!ready ? (
        <Splash />
      ) : (
        <>
          <Header />
          <StatusBar model={model} mode={mode} status={status} />
          <ChatFeed
            items={items}
            thinking={thinking}
            onSubmit={submit}
            onOpenPalette={() => setPaletteOpen(true)}
          />
          <ToolPanel actions={actions} />
        </>
      )}
      {box ? <SubWindow title={box.title} lines={box.lines} /> : null}
      {ask ? <Gatekeeper ask={ask} onAnswer={handleAnswer} /> : null}
      {paletteOpen ? (
        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onPick={handlePick} />
      ) : null}
      {pickerOpen ? (
        <ModelPicker open={pickerOpen} onClose={() => setPickerOpen(false)} onPick={handleModelPick} />
      ) : null}
      <Footer />
    </Box>
  );
}
