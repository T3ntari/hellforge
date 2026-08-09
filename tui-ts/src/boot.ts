/** Boot-time environment checks for the HELL'S CODE TUI splash checklist.
 *  Everything is local (no network beyond localhost) and fails soft: a
 *  failed check renders as ✗ on the splash, never blocks the app. */

import { spawnSync } from "node:child_process";

export type CheckState = "pending" | "ok" | "fail";

export interface BootCheck {
  id: string;
  label: string;
  state: CheckState;
  detail?: string;
}

/** `python --version` — the bridge spawns `python run.py bridge`. */
export function checkPython(): BootCheck {
  try {
    const r = spawnSync("python", ["--version"], { timeout: 5000, encoding: "utf8" });
    const v = `${r.stdout ?? ""}${r.stderr ?? ""}`.trim();
    return {
      id: "python",
      label: "python",
      state: r.status === 0 && /Python \d+\.\d+/.test(v) ? "ok" : "fail",
      detail: v || "not found",
    };
  } catch {
    return { id: "python", label: "python", state: "fail", detail: "not found" };
  }
}

/** Current git branch for the status bar ("?" when not a repo). */
export function currentBranch(): string {
  try {
    const r = spawnSync("git", ["rev-parse", "--abbrev-ref", "HEAD"], {
      timeout: 5000,
      encoding: "utf8",
    });
    return r.status === 0 && r.stdout ? r.stdout.trim() : "?";
  } catch {
    return "?";
  }
}

/** Local ollama detection — localhost only, no phone-home. */
export async function checkOllama(timeoutMs = 1500): Promise<BootCheck> {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    const res = await fetch("http://localhost:11434/api/tags", { signal: ctrl.signal });
    clearTimeout(t);
    let detail = "up";
    if (res.ok) {
      try {
        const j = (await res.json()) as { models?: unknown[] };
        detail = `${j.models?.length ?? 0} model(s)`;
      } catch {
        /* keep "up" */
      }
    }
    return { id: "ollama", label: "ollama", state: res.ok ? "ok" : "fail", detail };
  } catch {
    return { id: "ollama", label: "ollama", state: "fail", detail: "not detected" };
  }
}
