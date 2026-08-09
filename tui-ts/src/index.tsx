#!/usr/bin/env node
import React from "react";
import { render } from "ink";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
import { Bridge } from "./bridge.js";
import App from "./App.js";

/** Walk up from this module until run.py is found (the project root). */
function projectRoot(): string {
  let root = path.dirname(fileURLToPath(import.meta.url));
  while (!fs.existsSync(path.join(root, "run.py")) && root !== "/") {
    root = path.dirname(root);
  }
  return root;
}

const bridge = new Bridge("python", projectRoot());
const { unmount, waitUntilExit } = render(
  <App bridge={bridge as never} />,
  { exitOnCtrlC: false },
);

// Every exit path leads here — the process must never linger holding the
// python bridge child.
function hardExit(code = 0) {
  try {
    bridge.dispose();
  } catch {
    /* noop */
  }
  setTimeout(() => process.exit(code), 50);
}

process.on("exit", () => {
  try {
    bridge.dispose();
  } catch {
    /* noop */
  }
});
process.on("SIGINT", () => hardExit(0));
process.on("SIGTERM", () => hardExit(0));

bridge.onExit?.((code) => hardExit(code ?? 0));

bridge.start();
// Ink's waitUntilExit is unreliable in some terminals — exit anyway.
waitUntilExit().then(() => hardExit(0));
setTimeout(() => {}, 0);
