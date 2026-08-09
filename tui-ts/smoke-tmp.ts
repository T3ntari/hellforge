import { spawnBridge } from "./dist/bridge.js";

const bridge = spawnBridge();
let done = false;
let ready = false;

const log = (m: string) => console.log(`[smoke] ${m}`);

bridge.on("system", (t) => log(`system: ${t}`));
bridge.on("mode", (t) => log(`mode: ${t}`));
bridge.on("feed", (f) => log(`feed(${f.color}): ${f.text}`));
bridge.on("thinking", (on) => log(`thinking: ${on}`));
bridge.on("done", () => { log("done"); done = true; bridge.quit(); });
bridge.on("ready", () => { log("ready"); ready = true; bridge.submit("hello"); });
bridge.on("error", (m) => log(`error: ${m}`));
bridge.on("exit", (code) => { log(`exit: ${code}`); });

setTimeout(() => {
  if (!ready) { log("TIMEOUT: never ready"); process.exit(1); }
  if (!done) { log("TIMEOUT: no done event"); process.exit(1); }
  process.exit(0);
}, 60000).unref();
