import * as path from "path";
import * as fs from "fs";
import {
  workspace,
  ExtensionContext,
  commands,
  window,
  StatusBarAlignment,
} from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

const HELLFORGE_MARKERS = ["ep.py", "run.py", "eshell.py"];

/** Common install locations to search when nothing else works. */
const COMMON_ROOTS = [
  "~/Downloads/E/piano-dsl",
  "~/Downloads/E",
  "~/piano-dsl",
  "~/hellforge",
  "~/projects/hellforge",
  "C:/hellforge",
  "C:/E",
  "D:/piano-dsl",
  "D:/hellforge",
  "D:/E",
];

function expandHome(p: string): string {
  if (p.startsWith("~/") || p === "~") {
    return path.join(process.env.HOME || process.env.USERPROFILE || "", p.slice(p === "~" ? 1 : 2));
  }
  return p;
}

function isHellforgeRoot(dir: string): boolean {
  return HELLFORGE_MARKERS.some((m) => fs.existsSync(path.join(dir, m)));
}

/**
 * Find the HELLFORGE project root using every strategy we have:
 *   1. Settings override: hellforge.projectPath
 *   2. Environment variable HELLFORGE_HOME
 *   3. Walk up from the ACTIVE FILE (works when a single .e file is open)
 *   4. Walk up from every workspace folder
 *   5. Common install locations
 * Returns the root, or undefined. Never guesses a broken path.
 */
function findHellforgeRoot(): string | undefined {
  // 1. User settings override
  const cfg = workspace.getConfiguration("hellforge");
  const configured: string | undefined = cfg.get("projectPath");
  if (configured) {
    const p = expandHome(configured);
    if (isHellforgeRoot(p)) return p;
  }

  // 2. Environment variable
  const envHome = process.env.HELLFORGE_HOME;
  if (envHome && isHellforgeRoot(envHome)) return envHome;

  // 3. Active editor file — walk up from the open document
  const active = window.activeTextEditor?.document.uri.fsPath;
  if (active) {
    let dir = path.dirname(active);
    for (let i = 0; i < 12; i++) {
      if (isHellforgeRoot(dir)) return dir;
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }

  // 4. Workspace folders — walk up from each
  for (const folder of workspace.workspaceFolders ?? []) {
    let dir = folder.uri.fsPath;
    for (let i = 0; i < 12; i++) {
      if (isHellforgeRoot(dir)) return dir;
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }

  // 5. Common install locations
  for (const c of COMMON_ROOTS) {
    const p = expandHome(c);
    if (isHellforgeRoot(p)) return p;
  }

  return undefined;
}

function pyCmd(): string {
  const cfg = workspace.getConfiguration("hellforge");
  const custom = cfg.get<string>("pythonPath");
  if (custom && custom.trim()) return custom.trim();
  return process.platform === "win32" ? "py" : "python3";
}

/** Quote a shell argument safely for terminal.sendText. */
function shellQuote(arg: string): string {
  return `"${arg.replace(/"/g, '\\"')}"`;
}

function runHellforge(args: string[], inWindow = false, cwd?: string) {
  const root = cwd || findHellforgeRoot();
  if (!root) {
    const searched = [
      "settings (hellforge.projectPath)",
      "env var HELLFORGE_HOME",
      "active file parents",
      "workspace folders",
      "common install paths",
    ].join(", ");
    window.showErrorMessage(
      `HELLFORGE not found. Searched: ${searched}. ` +
        `Open a workspace containing ep.py, set HELLFORGE_HOME, or set hellforge.projectPath in settings.`,
    );
    return;
  }

  const runner = path.join(root, "run.py");
  const quoted = [shellQuote(runner), ...args.map(shellQuote)].join(" ");
  const cmd = `${pyCmd()} ${quoted}`;
  const name = inWindow ? `HELLFORGE: ${args[0]}` : "HELLFORGE";
  // Tell the shell where HELLFORGE lives: cwd + HELLFORGE_PROJECT env var
  const env = { ...process.env, HELLFORGE_PROJECT: root } as { [key: string]: string };
  const term = window.createTerminal({ name, cwd: root, env });
  term.sendText(cmd);
  term.show();
}

/** Open the HELLFORGE shell honoring the hellforge.shellType setting. */
function openShell() {
  const cfg = workspace.getConfiguration("hellforge");
  const shellType = cfg.get<string>("shellType") || "eshell";
  if (shellType === "hshell") {
    runHellforge(["shell", "--project", findHellforgeRoot() || ""], true);
  } else {
    const root = findHellforgeRoot();
    if (!root) {
      window.showErrorMessage(
        "HELLFORGE not found. Set hellforge.projectPath in settings or open a workspace with ep.py.",
      );
      return;
    }
    const env = { ...process.env, HELLFORGE_PROJECT: root } as { [key: string]: string };
    const term = window.createTerminal({
      name: "HELLFORGE",
      cwd: root,
      env,
      shellPath: pyCmd(),
      shellArgs: [path.join(root, "eshell.py")],
    });
    term.show();
  }
}

export function activate(context: ExtensionContext) {
  const activeFile = () => window.activeTextEditor?.document.uri.fsPath;

  // Always-on status bar buttons → open the HELLFORGE quick menu (any file, any time)
  const status = window.createStatusBarItem(StatusBarAlignment.Right, 100);
  status.text = "$(terminal) HELLFORGE";
  status.tooltip = "HELLFORGE: Open Shell / Settings / Convert";
  status.command = "hellforge.menu";
  status.show();
  context.subscriptions.push(status);

  const gear = window.createStatusBarItem(StatusBarAlignment.Right, 99);
  gear.text = "$(gear)";
  gear.tooltip = "HELLFORGE Settings";
  gear.command = "hellforge.settings";
  gear.show();
  context.subscriptions.push(gear);

  // Bridge request channel: client -> server -> Python bridge
  let bridgeRequester: (method: string, params: any) => Promise<any> = async () => null;
  const bridgeRequestCommand = commands.registerCommand("hellforge.bridgeRequest", (method: string, params: any) =>
    bridgeRequester(method, params),
  );
  context.subscriptions.push(bridgeRequestCommand);

  context.subscriptions.push(
    commands.registerCommand("hellforge.play", async () => {
      let f = activeFile();
      if (!f || !/\.(e|ei|eic|enx|eci|machine|human|mid|wav|mp3|mp4)$/i.test(f)) {
        const picked = await window.showOpenDialog({
          canSelectMany: false,
          filters: {
            "HELLFORGE files": ["e", "ei", "eic", "enx", "eci", "machine", "human"],
            "Audio/MIDI": ["mid", "midi", "wav", "mp3", "mp4"],
          },
        });
        if (!picked || picked.length === 0) return;
        f = picked[0].fsPath;
      }
      if (f) runHellforge(["play", f]);
    }),
    commands.registerCommand("hellforge.playWindow", async () => {
      let f = activeFile();
      if (!f || !/\.(e|ei|eic|enx|eci|machine|human|mid|wav|mp3|mp4)$/i.test(f)) {
        const picked = await window.showOpenDialog({
          canSelectMany: false,
          filters: { "HELLFORGE files": ["e", "ei", "eic", "enx", "eci"], "Audio/MIDI": ["mid", "wav", "mp3"] },
        });
        if (!picked || picked.length === 0) return;
        f = picked[0].fsPath;
      }
      if (f) runHellforge(["play", f, "--gui"], true);
    }),
    commands.registerCommand("hellforge.openShell", () => {
      openShell();
    }),
    commands.registerCommand("hellforge.selectShell", async () => {
      const pick = await window.showQuickPick(
        [
          { label: "$(terminal) eshell", description: "Integrated VS Code terminal", value: "eshell" },
          { label: "$(terminal) hshell", description: "Separate native window", value: "hshell" },
        ],
        { placeHolder: "Choose the HELLFORGE shell" },
      );
      if (pick) {
        await workspace.getConfiguration("hellforge").update("shellType", pick.value, true);
        openShell();
      }
    }),
    commands.registerCommand("hellforge.settings", () => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { SettingsPanel } = require("./settingsPanel") as typeof import("./settingsPanel");
      SettingsPanel.createOrShow(context.extensionUri);
    }),
    commands.registerCommand("hellforge.menu", async () => {
      const pick = await window.showQuickPick(
        [
          { label: "$(terminal) Open E Shell", value: "shell" },
          { label: "$(settings-gear) Open Settings", value: "settings", detail: "Memory, threads, GPU acceleration, eshell path" },
          { label: "$(arrow-swap) Convert Syntax", value: "convert", detail: "v1 / v2 / v3 / v4" },
          { label: "$(play) Play", value: "play" },
        ],
        { placeHolder: "HELLFORGE — choose an action" },
      );
      if (!pick) return;
      if (pick.value === "shell") await commands.executeCommand("hellforge.openShell");
      else if (pick.value === "settings") await commands.executeCommand("hellforge.settings");
      else if (pick.value === "convert") await commands.executeCommand("hellforge.convert");
      else if (pick.value === "play") await commands.executeCommand("hellforge.play");
    }),
    commands.registerCommand("hellforge.convert", () => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { convertActiveFile } = require("./convert") as typeof import("./convert");
      void convertActiveFile(bridgeRequester);
    }),
  );

  // Auto-compile on save (opt-in setting)
  const saveDisposable = workspace.onDidSaveTextDocument((doc) => {
    const cfg = workspace.getConfiguration("hellforge");
    if (!cfg.get<boolean>("autoCompileOnSave")) return;
    if (!/\.(e|ei|eic|enx|eci)$/i.test(doc.fileName)) return;
    runHellforge(["compile", doc.fileName, "-o", `${doc.fileName}.mid`]);
  });
  context.subscriptions.push(saveDisposable);

  // LSP client — compiled server lives in server/out/server.js (tsconfig outDir)
  const serverModule = context.asAbsolutePath(path.join("server", "out", "server.js"));
  if (!fs.existsSync(serverModule)) {
    window.showErrorMessage(
      `HELLFORGE LSP server missing: ${serverModule}. Reinstall the extension.`,
    );
    return;
  }
  const serverOptions: ServerOptions = {
    run: { module: serverModule, transport: TransportKind.ipc },
    debug: {
      module: serverModule,
      transport: TransportKind.ipc,
      options: { execArgv: ["--nolazy", "--inspect=6009"] },
    },
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "e" }],
    synchronize: { fileEvents: workspace.createFileSystemWatcher("**/*.{e,ei,eic,enx,eci,machine,human}") },
  };

  client = new LanguageClient("hellforgeLanguage", "HELLFORGE E Language", serverOptions, clientOptions);
  client.start();

  // Surface bridge failures (lint/completions disabled) instead of silence
  client.onNotification("hellforge/bridgeDown", () => {
    window.showErrorMessage(
      "HELLFORGE bridge failed to start — linting and completions are disabled. " +
        "Check the HELLFORGE Language Server output channel for details.",
    );
  });

  // Route bridge requests (settings GUI, conversion) through the LSP server
  bridgeRequester = (method: string, params: any): Promise<any> =>
    client
      ? (client.sendRequest("hellforge/bridgeRequest", { method, params }) as Promise<any>)
      : Promise.resolve(null);
}

export function deactivate(): Thenable<void> | undefined {
  return client?.stop();
}
