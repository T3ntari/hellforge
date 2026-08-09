import { spawn, ChildProcess } from "node:child_process";
import { PyToTs, TsToPy, AskState } from "./protocol.js";

type Handler = (msg: PyToTs) => void;

/** Spawns `python run.py bridge` and speaks the JSON-lines protocol. */
export class Bridge {
  private proc: ChildProcess | null = null;
  private buffer = "";
  private ready = false;
  private handlers = new Map<string, Handler[]>();
  private pending: TsToPy[] = [];

  constructor(
    private pythonBin = "python",
    private cwd: string = process.cwd(),
  ) {}

  on<E extends PyToTs["type"]>(event: E, handler: (msg: Extract<PyToTs, { type: E }>) => void) {
    const list = this.handlers.get(event) ?? [];
    list.push(handler as Handler);
    this.handlers.set(event, list);
    return () => {
      const l = this.handlers.get(event) ?? [];
      this.handlers.set(event, l.filter((h) => h !== handler));
    };
  }

  private emit(msg: PyToTs) {
    (this.handlers.get(msg.type) ?? []).forEach((h) => h(msg));
  }

  start() {
    this.proc = spawn(this.pythonBin, ["run.py", "bridge"], {
      cwd: this.cwd,
      stdio: ["pipe", "pipe", "pipe"],
    });
    this.proc.stdout!.on("data", (chunk: Buffer) => {
      this.buffer += chunk.toString("utf-8");
      let idx: number;
      while ((idx = this.buffer.indexOf("\n")) >= 0) {
        const line = this.buffer.slice(0, idx).trim();
        this.buffer = this.buffer.slice(idx + 1);
        if (!line) continue;
        try {
          this.emit(JSON.parse(line) as PyToTs);
        } catch {
          /* ignore malformed lines */
        }
      }
    });
    this.proc.stderr!.on("data", (d: Buffer) => {
      process.stderr.write(d);
    });
    this.proc.on("close", () => {
      this.ready = false;
    });
    this.ready = true;
    // flush anything queued before the process was up
    this.pending.forEach((m) => this.send(m));
    this.pending = [];
  }

  private send(msg: TsToPy) {
    if (!this.proc || !this.ready) {
      this.pending.push(msg);
      return;
    }
    this.proc.stdin!.write(JSON.stringify(msg) + "\n");
  }

  submit(line: string) {
    this.send({ type: "submit", line });
  }

  answer(key: string, value: "y" | "n" | "e") {
    this.send({ type: "answer", key, value });
  }

  quit() {
    this.send({ type: "quit" });
  }

  dispose() {
    try {
      this.proc?.stdin?.end();
    } catch {
      /* noop */
    }
    try {
      this.proc?.kill("SIGTERM");
    } catch {
      /* noop */
    }
  }
}

export type { AskState };
