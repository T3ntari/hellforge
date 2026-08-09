import { spawn } from "node:child_process";
/** Spawns `python run.py bridge` and speaks the JSON-lines protocol. */
export class Bridge {
    pythonBin;
    cwd;
    proc = null;
    buffer = "";
    ready = false;
    handlers = new Map();
    pending = [];
    constructor(pythonBin = "python", cwd = process.cwd()) {
        this.pythonBin = pythonBin;
        this.cwd = cwd;
    }
    on(event, handler) {
        const list = this.handlers.get(event) ?? [];
        list.push(handler);
        this.handlers.set(event, list);
        return () => {
            const l = this.handlers.get(event) ?? [];
            this.handlers.set(event, l.filter((h) => h !== handler));
        };
    }
    emit(msg) {
        (this.handlers.get(msg.type) ?? []).forEach((h) => h(msg));
    }
    start() {
        this.proc = spawn(this.pythonBin, ["run.py", "bridge"], {
            cwd: this.cwd,
            stdio: ["pipe", "pipe", "pipe"],
        });
        this.proc.stdout.on("data", (chunk) => {
            this.buffer += chunk.toString("utf-8");
            let idx;
            while ((idx = this.buffer.indexOf("\n")) >= 0) {
                const line = this.buffer.slice(0, idx).trim();
                this.buffer = this.buffer.slice(idx + 1);
                if (!line)
                    continue;
                try {
                    this.emit(JSON.parse(line));
                }
                catch {
                    /* ignore malformed lines */
                }
            }
        });
        this.proc.stderr.on("data", (d) => {
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
    send(msg) {
        if (!this.proc || !this.ready) {
            this.pending.push(msg);
            return;
        }
        this.proc.stdin.write(JSON.stringify(msg) + "\n");
    }
    submit(line) {
        this.send({ type: "submit", line });
    }
    answer(key, value) {
        this.send({ type: "answer", key, value });
    }
    quit() {
        this.send({ type: "quit" });
    }
    dispose() {
        try {
            this.proc?.stdin?.end();
        }
        catch {
            /* noop */
        }
        try {
            this.proc?.kill("SIGTERM");
        }
        catch {
            /* noop */
        }
    }
}
