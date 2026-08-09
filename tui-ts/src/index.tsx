import React from "react";
import { render } from "ink";
import { Bridge } from "./bridge.js";
import App from "./App.js";

const bridge = new Bridge("python", process.cwd());
const { unmount, waitUntilExit } = render(
  <App bridge={bridge as never} />,
  { exitOnCtrlC: false },
);

process.on("exit", () => bridge.dispose());
process.on("SIGINT", () => bridge.quit());
process.on("SIGTERM", () => bridge.quit());

bridge.start();
waitUntilExit().then(() => process.exit(0));
