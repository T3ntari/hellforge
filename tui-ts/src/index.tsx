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

process.on("exit", () => bridge.dispose());
process.on("SIGINT", () => bridge.quit());
process.on("SIGTERM", () => bridge.quit());

bridge.start();
waitUntilExit().then(() => process.exit(0));
