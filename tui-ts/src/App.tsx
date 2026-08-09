/** HELL'S CODE TUI root (Ink). Owned by tickets-ts-engine.
 *  Wires the bridge events into App state and renders the component tree.
 *  Component contracts are documented in each placeholder under
 *  src/components/ — the owning agents replace the placeholders wholesale.
 *
 *  bridge prop (from index.ts, see tickets-ts-bridge): a typed emitter
 *  with `on<Event>(type, handler)` subscriptions per PyToTs type plus
 *  submit()/answer()/quit() senders (see BridgeLike below). */
import { Box, Text, useApp, useInput } from "ink";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import type { AskState, Color, FeedItem, PyToTs } from "./protocol.js";
import { feedReducer, type ToolAction } from "./frame.js";
import { useInputEditor } from "./input.js";
import { checkOllama, checkPython, currentBranch, type BootCheck } from "./boot.js";
import { tokenHex } from "./theme.js";
import ChatFeed from "./components/ChatFeed.js";
import { CommandPalette } from "./components/CommandPalette.js";
import Footer from "./components/Footer.js";
import { Gatekeeper } from "./components/Gatekeeper.js";
import Header from "./components/Header.js";
import { ModelPicker } from "./components/ModelPicker.js";
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
  const [checks, setChecks] = useState<BootCheck[]>([]);
  const [version, setVersion] = useState("");
  const [branch, setBranch] = useState("");
  const [files, setFiles] = useState<string[]>([]);
  const tokensRef = useRef(0);
  const [tokens, setTokens] = useState(0);

  useEffect(() => {
    setBranch(currentBranch());
    setChecks([
      checkPython(),
      { id: "bridge", label: "bridge", state: "pending" },
      { id: "model", label: "model", state: "pending" },
      { id: "ollama", label: "ollama", state: "pending" },
    ]);
    checkOllama().then((o) => setChecks((c) => c.map((x) => (x.id === "ollama" ? o : x))));
  }, []);

  const submit = useCallback(
    (line: string) => {
      if (!line.trim()) return;
      bridge.submit(line);
    },
    [bridge],
  );

  // Input line. The feed agent's ChatFeed does not host an editor, so the
  // line lives here in App (raw keys via ../input.ts). A leading "/" opens
  // the command palette; Esc/Enter inside the palette are its own.
  const editorActive = ready && !ask && !paletteOpen && !pickerOpen;
  const editor = useInputEditor({
    isActive: editorActive,
    onSubmit: (line) => {
      submit(line);
      editor.clear();
    },
  });
  const slashWasOn = useRef(false);
  useEffect(() => {
    const buf = editor.state.buffer;
    if (buf === "/") {
      if (!slashWasOn.current) setPaletteOpen(true);
      slashWasOn.current = true;
    } else {
      if (slashWasOn.current && paletteOpen) setPaletteOpen(false);
      slashWasOn.current = false;
    }
  }, [editor.state.buffer, paletteOpen]);

  useEffect(() => {
    bridge.on("system", (m) => {
      const text = m.text ?? "";
      const v = /v\d+\.\d+(?:\.\d+)?/.exec(text);
      if (v) setVersion(v[0]);
      const mod = parseModel(text);
      setModel(mod);
      dispatch({ type: "append", item: { color: "dim", text } });
      setChecks((c) =>
        c.map((x) =>
          x.id === "bridge"
            ? { ...x, state: "ok", detail: "ready" }
            : x.id === "model"
              ? { ...x, state: mod !== "?" ? "ok" : "fail", detail: mod }
              : x,
        ),
      );
      setReady(true);
    });
    bridge.on("chunk", (m) => {
      tokensRef.current += (m.text ?? "").length / 4;
      setTokens(Math.round(tokensRef.current));
      dispatch({ type: "chunk", text: m.text ?? "", color: null });
      setReady(true);
    });
    bridge.on("feed", (m) => {
      const t = m.text ?? "";
      const fm = /^\s{2}(read|write|edit|delete)\s+(\S+)/.exec(t);
      if (fm) setFiles((f) => [...new Set([...f, fm[2]])].slice(-4));
      dispatch({
        type: "append",
        item: { color: (m.color as Color | null) ?? null, text: t },
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

  const handleAnswer = useCallback(
    (key: string, value: "y" | "n" | "e") => {
      bridge.answer(key, value);
      setAsk(null);
    },
    [bridge],
  );

  const handleType = useCallback((char: string) => {
    // Typing while the palette is open: close it and continue editing
    // (e.g. "/" then "e" → "/e" → "/exit").
    setPaletteOpen(false);
    editor.setState((prev) => ({
      buffer: prev.buffer + char,
      cursor: prev.cursor + 1,
    }));
  }, [editor]);

  const handlePick = useCallback((command: string) => {
      if (command === "/model") {
        setPickerOpen(true);
        return;
      }
      if (QUIT_COMMANDS.has(command)) {
        bridge.quit();
        return;
      }
      // Insert the picked command into the input line so the user can
      // append arguments (e.g. "/fix <task>") — Enter submits the line.
      editor.setState({ buffer: command, cursor: command.length });
    },
    [bridge, editor],
  );

  const handleModelPick = useCallback((_provider: string, _model: string) => {
    // The stdio protocol has no model-change message yet — the picker is a
    // local UI for now. Wire a submit/answer channel here when the bridge
    // grows one (see ModelPicker placeholder note).
    setPickerOpen(false);
  }, []);

  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      // While the input editor is active, Ctrl+C is copy (input.ts); quit
      // only when no editor is taking keys (ask/palette/picker up).
      if (editorActive) return;
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
    if (paletteOpen) {
      setPaletteOpen(false);
    }
  });

  return (
    <Box flexDirection="column" height="100%">
      {!ready ? (
        <Splash status="starting agent bridge..." version={version} checks={checks} />
      ) : (
        <>
          <Header />
          <StatusBar
            model={model}
            mode={mode}
            status={status}
            branch={branch}
            files={files}
            tokens={tokens}
          />
          <ChatFeed items={items} thinking={thinking} />
          <ToolPanel
            actions={actions.map((a) => ({
              title: a.title,
              status: (a.done ? "done" : "running") as "done" | "running",
            }))}
          />
          <Box>
            <Text color={tokenHex("accent")}>❯ </Text>
            <Text color={tokenHex("text")}>
              {editor.state.buffer.slice(0, editor.state.cursor)}
              <Text inverse>{editor.state.buffer[editor.state.cursor] ?? " "}</Text>
              {editor.state.buffer.slice(editor.state.cursor + 1)}
            </Text>
          </Box>
        </>
      )}
      {box ? <SubWindow title={box.title} lines={box.lines} /> : null}
      {ask ? <Gatekeeper ask={ask} onAnswer={(v) => handleAnswer(ask!.key, v)} /> : null}
      {paletteOpen ? (
        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onPick={handlePick} onType={handleType} />
      ) : null}
      {pickerOpen ? (
        <ModelPicker open={pickerOpen} onClose={() => setPickerOpen(false)} onPick={handleModelPick} />
      ) : null}
      <Footer />
    </Box>
  );
}
