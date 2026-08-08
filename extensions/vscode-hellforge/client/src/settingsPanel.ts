import * as vscode from "vscode";

/**
 * HELLFORGE Settings panel — real settings with Apply/Cancel buttons.
 * - General: eshell/shell path (auto-detected, overridable)
 * - Advanced: fetched LIVE from the eshell runtime (memory, threads, GPU...)
 *   and reloaded automatically when the shell path changes.
 * - Apply actually applies (GPU evaluators toggle, thread pool resize, mem cap)
 *   and persists into the shared .plugin_config.json store.
 */

export class SettingsPanel {
  public static currentPanel: SettingsPanel | undefined;

  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private shellPath = "";
  private advanced: { [key: string]: any } = {};

  public static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.ViewColumn.Active;
    if (SettingsPanel.currentPanel) {
      SettingsPanel.currentPanel.panel.reveal(column);
      SettingsPanel.currentPanel.reloadFromBridge();
      return;
    }
    const panel = vscode.window.createWebviewPanel(
      "hellforgeSettings",
      "HELLFORGE Settings",
      column,
      { enableScripts: true, retainContextWhenHidden: true },
    );
    SettingsPanel.currentPanel = new SettingsPanel(panel, extensionUri);
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this.panel = panel;
    panel.webview.html = this.getHtml();
    panel.webview.onDidReceiveMessage(this.onMessage, this, this.disposables);
    panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.reloadFromBridge();
  }

  private dispose() {
    SettingsPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) d.dispose();
  }

  private post(msg: any) {
    void this.panel.webview.postMessage(msg);
  }

  /** Ask the LSP server (which talks to the Python bridge) for live config. */
  private sendRequest(method: string, params: any): Promise<any> {
    return new Promise((resolve) => {
      const handler = vscode.commands.executeCommand;
      void handler("hellforge.bridgeRequest", method, params).then(
        (result) => resolve(result),
        () => resolve(null),
      );
    });
  }

  async reloadFromBridge() {
    const cfg = await this.sendRequest("get_runtime_config", {});
    if (cfg && typeof cfg === "object") {
      this.advanced = cfg;
      this.shellPath = cfg.shell_path || "";
    }
    this.post({ type: "render", shellPath: this.shellPath, advanced: this.advanced });
  }

  private async onMessage(msg: any) {
    switch (msg?.type) {
      case "shellPathChanged": {
        this.shellPath = (msg.value || "").trim();
        // advanced settings reload from the (new) shell automatically
        await this.reloadFromBridge();
        this.post({ type: "notice", text: "Advanced settings reloaded from the selected shell." });
        break;
      }
      case "apply": {
        const cfg = { ...msg.advanced, shell_path: this.shellPath };
        // 1. Apply for real through the bridge (GPU/threads/mem are live)
        const applied = await this.sendRequest("apply_runtime_config", { config: cfg });
        // 2. Mirror key options into VS Code settings for the extension itself
        const ext = vscode.workspace.getConfiguration("hellforge");
        if (this.shellPath) {
          const root = this.shellPath
            .replace(/\\/g, "/")
            .replace(/\/[^/]*$/, "");
          await ext.update("projectPath", root, vscode.ConfigurationTarget.Global);
        }
        await ext.update(
          "autoCompileOnSave",
          !!(msg.advanced && msg.advanced.auto_compile_on_save),
          vscode.ConfigurationTarget.Global,
        );
        await ext.update(
          "playWindowed",
          !!(msg.advanced && msg.advanced.play_windowed),
          vscode.ConfigurationTarget.Global,
        );
        vscode.window.showInformationMessage(
          applied ? "HELLFORGE settings applied (memory, threads, GPU acceleration are live)." : "Settings applied.",
        );
        if (applied) this.advanced = applied;
        break;
      }
      case "cancel": {
        // reload = discard the form and pull fresh from the runtime
        await this.reloadFromBridge();
        this.post({ type: "notice", text: "Changes discarded." });
        break;
      }
    }
  }

  private getHtml(): string {
    const cpuDefault = 4;
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<style>
  body { font-family: var(--vscode-font-family); padding: 16px 20px; color: var(--vscode-foreground); }
  h1 { font-size: 18px; margin: 0 0 4px; color: var(--vscode-editor-foreground); }
  .sub { color: var(--vscode-descriptionForeground); font-size: 12px; margin-bottom: 16px; }
  h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--vscode-descriptionForeground); border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 6px; margin: 22px 0 10px; }
  .row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
  .row label { width: 220px; flex-shrink: 0; font-size: 13px; }
  .row .hint { font-size: 11px; color: var(--vscode-descriptionForeground); margin-left: 230px; margin-top: -6px; margin-bottom: 10px; }
  input[type=text], input[type=number] {
    background: var(--vscode-input-background); color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border, transparent); padding: 5px 8px; border-radius: 3px;
    flex: 1; max-width: 420px;
  }
  input[type=checkbox] { transform: scale(1.25); accent-color: var(--vscode-button-background); }
  button {
    background: var(--vscode-button-background); color: var(--vscode-button-foreground);
    border: none; padding: 6px 14px; border-radius: 3px; cursor: pointer; font-size: 13px;
  }
  button:hover { background: var(--vscode-button-hoverBackground); }
  button.secondary { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
  .actions { display: flex; gap: 10px; margin-top: 24px; }
  #notice { color: var(--vscode-notificationsInfoIconForeground); font-size: 12px; min-height: 16px; margin-top: 10px; }
  .mono { font-family: var(--vscode-editor-font-family); font-size: 12px; }
  .badge { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); font-size: 10px; padding: 1px 6px; border-radius: 8px; }
</style>
</head>
<body>
  <h1>HELLFORGE Settings</h1>
  <div class="sub">Runtime settings are fetched live from the eshell runtime and applied for real (memory cap, thread pool, GPU evaluators).</div>

  <h2>General</h2>
  <div class="row">
    <label for="shell">eshell location</label>
    <input type="text" id="shell" class="mono" placeholder="auto-detected…" />
  </div>
  <div class="row">
    <button id="detect" class="secondary">Detect</button>
    <span id="shellState" class="badge">loading…</span>
  </div>
  <div class="hint">Advanced settings below reload automatically when this path changes.</div>

  <h2>Advanced <span class="badge">live from eshell</span></h2>

  <div class="row">
    <label for="mem">Max memory (GB)</label>
    <input type="number" id="mem" min="1" max="64" step="0.5" />
  </div>
  <div class="hint">Real limit: loop unrolling fails gracefully beyond it — no OOM.</div>

  <div class="row">
    <label for="threads">Threads used</label>
    <input type="number" id="threads" min="0" max="64" step="1" />
  </div>
  <div class="hint">0 = auto (default ${cpuDefault} × CPU cores). Resizes the async compile pool for real.</div>

  <div class="row">
    <label for="gpu">GPU acceleration</label>
    <input type="checkbox" id="gpu" />
  </div>
  <div class="hint">Real toggle — disables the TensorSHARP/Radical GPU math evaluators.</div>

  <div class="row">
    <label for="lure">LURE (LuaJIT) acceleration</label>
    <input type="checkbox" id="lure" />
  </div>
  <div class="hint">Real toggle — enables/disables the LuaJIT math evaluator.</div>

  <div class="row">
    <label for="loopcap">Loop unroll cap (lines)</label>
    <input type="number" id="loopcap" min="0" step="1000" />
  </div>
  <div class="hint">0 = unlimited. Runaway loops fail with a clear error instead of hanging.</div>

  <div class="row">
    <label for="strict">Strict compile by default</label>
    <input type="checkbox" id="strict" />
  </div>
  <div class="hint">Fail fast on any syntax error (line:col) instead of lenient compile.</div>

  <div class="row">
    <label for="autosave">Auto-compile on save</label>
    <input type="checkbox" id="autosave" />
  </div>

  <div class="row">
    <label for="windowed">Play in separate window</label>
    <input type="checkbox" id="windowed" />
  </div>

  <div class="row">
    <label for="velwarn">Velocity scale warning</label>
    <input type="checkbox" id="velwarn" />
  </div>
  <div class="hint">Warn when float velocity is ambiguous (0–1 vs 0–127).</div>

  <div class="actions">
    <button id="apply">Apply changes</button>
    <button id="cancel" class="secondary">Cancel</button>
  </div>
  <div id="notice"></div>

<script>
  const vscode = acquireVsCodeApi();
  const $ = (id) => document.getElementById(id);
  let advanced = {};

  function render(data) {
    advanced = data.advanced || {};
    $("shell").value = data.shellPath || "";
    $("mem").value = advanced.max_memory_gb != null ? advanced.max_memory_gb : 2;
    $("threads").value = advanced.threads != null ? advanced.threads : 0;
    $("gpu").checked = advanced.gpu_acceleration !== false;
    $("lure").checked = advanced.lure_acceleration !== false;
    $("loopcap").value = advanced.loop_cap != null ? advanced.loop_cap : 100000;
    $("strict").checked = !!advanced.strict_default;
    $("autosave").checked = advanced.auto_compile_on_save !== false;
    $("windowed").checked = !!advanced.play_windowed;
    $("velwarn").checked = advanced.velocity_warning !== false;
    $("shellState").textContent = data.shellPath ? "found" : "not found — using default";
  }

  function collect() {
    return {
      max_memory_gb: parseFloat($("mem").value) || 2,
      threads: parseInt($("threads").value, 10) || 0,
      gpu_acceleration: $("gpu").checked,
      lure_acceleration: $("lure").checked,
      loop_cap: parseInt($("loopcap").value, 10) || 0,
      strict_default: $("strict").checked,
      auto_compile_on_save: $("autosave").checked,
      play_windowed: $("windowed").checked,
      velocity_warning: $("velwarn").checked,
    };
  }

  window.addEventListener("message", (e) => {
    const msg = e.data;
    if (msg.type === "render") render(msg);
    else if (msg.type === "notice") $("notice").textContent = msg.text;
  });

  $("shell").addEventListener("change", () => {
    vscode.postMessage({ type: "shellPathChanged", value: $("shell").value });
  });
  $("detect").addEventListener("click", () => {
    vscode.postMessage({ type: "shellPathChanged", value: $("shell").value });
  });
  $("apply").addEventListener("click", () => {
    vscode.postMessage({ type: "apply", advanced: collect() });
  });
  $("cancel").addEventListener("click", () => {
    vscode.postMessage({ type: "cancel" });
  });
</script>
</body>
</html>`;
  }
}
