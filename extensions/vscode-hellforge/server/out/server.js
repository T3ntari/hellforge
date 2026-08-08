"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const node_1 = require("vscode-languageserver/node");
const vscode_languageserver_textdocument_1 = require("vscode-languageserver-textdocument");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const connection = (0, node_1.createConnection)(node_1.ProposedFeatures.all);
const documents = new node_1.TextDocuments(vscode_languageserver_textdocument_1.TextDocument);
let bridgePath;
function findBridgePy() {
    // Bundled copy inside the extension (packaged with the .vsix).
    // __dirname = <ext>/server/out  →  one level up = <ext>/server/resources
    const bundled = path.join(__dirname, "..", "resources", "lsp_bridge.py");
    if (fs.existsSync(bundled))
        return bundled;
    // Dev checkout: walk up from the server out dir looking for tools/lsp_bridge.py
    let dir = path.resolve(__dirname);
    for (let i = 0; i < 12; i++) {
        const candidate = path.join(dir, "tools", "lsp_bridge.py");
        if (fs.existsSync(candidate))
            return candidate;
        const parent = path.dirname(dir);
        if (parent === dir)
            return undefined;
        dir = parent;
    }
    return undefined;
}
function pyCmd() {
    return process.platform === "win32" ? "py" : "python3";
}
function findPython() {
    // execFile needs a real executable on PATH; try several names.
    const candidates = process.platform === "win32"
        ? ["py", "python", "python3"]
        : ["python3", "python"];
    for (const c of candidates) {
        try {
            require("child_process").execFileSync(c, ["--version"], {
                stdio: "ignore",
                timeout: 3000,
            });
            return c;
        }
        catch {
            /* try next */
        }
    }
    return undefined;
}
/**
 * Persistent bridge process — one long-lived Python process speaking
 * JSON-RPC over stdin/stdout. Spawning Python per request was fragile
 * (PATH lookup, spawn cost, 5s timeout); this keeps the bridge warm and
 * makes the whole LSP pipeline ~10x faster. Auto-restarts on crash.
 */
let bridgeProc;
let bridgeReqId = 0;
const bridgePending = new Map();
let bridgeBuf = "";
let bridgeDead = false;
function startBridge() {
    const bridge = bridgePath || findBridgePy();
    const py = findPython() || pyCmd();
    if (!bridge) {
        connection.console.error(`[hellforge] bridge missing: ${bridge}`);
        return false;
    }
    const proc = require("child_process").spawn(py, [bridge], {
        cwd: path.dirname(bridge),
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
    });
    bridgeProc = proc;
    bridgeDead = false;
    proc.stdout.on("data", (chunk) => {
        bridgeBuf += chunk.toString("utf8");
        let nl = bridgeBuf.indexOf("\n");
        while (nl >= 0) {
            const line = bridgeBuf.slice(0, nl).trim();
            bridgeBuf = bridgeBuf.slice(nl + 1);
            if (line.startsWith("{")) {
                try {
                    const msg = JSON.parse(line);
                    const cb = bridgePending.get(msg.id);
                    if (cb) {
                        bridgePending.delete(msg.id);
                        cb(msg.result ?? msg.error ?? null);
                    }
                }
                catch {
                    /* skip malformed line */
                }
            }
            nl = bridgeBuf.indexOf("\n");
        }
    });
    proc.stderr.on("data", (chunk) => {
        connection.console.error(`[hellforge:bridge] ${chunk.toString().trim()}`);
    });
    proc.on("exit", () => {
        bridgeProc = undefined;
        for (const cb of bridgePending.values())
            cb(null);
        bridgePending.clear();
    });
    return true;
}
function callBridge(method, params) {
    return new Promise((resolve) => {
        if (!bridgeProc) {
            if (!startBridge()) {
                resolve(null);
                return;
            }
        }
        if (bridgeDead || !bridgeProc || bridgeProc.stdin.destroyed) {
            resolve(null);
            return;
        }
        const id = ++bridgeReqId;
        bridgePending.set(id, (v) => resolve(v));
        bridgeProc.stdin.write(JSON.stringify({ id, method, params }) + "\n");
        // safety net: never hang forever waiting on a stuck bridge
        setTimeout(() => {
            if (bridgePending.has(id)) {
                bridgePending.delete(id);
                resolve(null);
            }
        }, 8000);
    });
}
connection.onInitialize((_params) => {
    bridgePath = findBridgePy();
    return {
        capabilities: {
            textDocumentSync: node_1.TextDocumentSyncKind.Full,
            completionProvider: { resolveProvider: false, triggerCharacters: ["@", "#", "$", "(", ",", "."] },
            hoverProvider: true,
            documentSymbolProvider: true,
            definitionProvider: true,
            documentFormattingProvider: true,
            signatureHelpProvider: { triggerCharacters: ["(", ","] },
        },
    };
});
connection.onInitialized(() => {
    connection.client.register(node_1.DidChangeConfigurationNotification.type, undefined);
    // Startup health check — surface bridge failures instead of failing silently
    void callBridge("get_runtime_config", {}).then((cfg) => {
        if (cfg && typeof cfg === "object" && "max_memory_gb" in cfg) {
            connection.console.info("[hellforge] bridge healthy (persistent process)");
        }
        else {
            connection.console.error("[hellforge] bridge health check FAILED — lint/completions disabled");
            void connection.sendNotification("hellforge/bridgeDown", {});
        }
    });
});
/**
 * Diagnostics service — linter output lands in VS Code's Problems panel.
 * - Debounced (300ms) so we don't spawn a Python process per keystroke.
 * - Runs on document open, change, and close (clears on close).
 * - Maps linter severity (0=fatal,1=error,2=warning,3=info) to LSP
 *   DiagnosticSeverity (1=Error,2=Warning,3=Information,4=Hint).
 */
function lspSeverity(s) {
    if (s === 0 || s === 1)
        return 1; // fatal/error → Error
    if (s === 2)
        return 2; // warning → Warning
    if (s === 3)
        return 3; // info → Information
    return 2;
}
const diagTimers = new Map();
function scheduleDiagnostics(uri) {
    const doc = documents.get(uri);
    if (!doc)
        return;
    const existing = diagTimers.get(uri);
    if (existing)
        clearTimeout(existing);
    diagTimers.set(uri, setTimeout(() => {
        diagTimers.delete(uri);
        const current = documents.get(uri);
        if (!current)
            return;
        const text = current.getText();
        callBridge("get_diagnostics", { text }).then((diags) => {
            if (!diags)
                return;
            const mapped = diags.map((d) => ({
                range: {
                    start: { line: d.line, character: d.char },
                    end: { line: d.line, character: d.char + (d.length || 1) },
                },
                message: d.message,
                severity: lspSeverity(d.severity),
                source: "hellforge",
            }));
            connection.sendDiagnostics({ uri, diagnostics: mapped });
        });
    }, 300));
}
documents.onDidOpen((e) => scheduleDiagnostics(e.document.uri));
documents.onDidChangeContent((e) => scheduleDiagnostics(e.document.uri));
documents.onDidClose((e) => {
    const t = diagTimers.get(e.document.uri);
    if (t)
        clearTimeout(t);
    diagTimers.delete(e.document.uri);
    connection.sendDiagnostics({ uri: e.document.uri, diagnostics: [] });
});
connection.onCompletion(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return [];
    const text = doc.getText();
    const pos = params.position;
    const result = await callBridge("get_completions", {
        text, line: pos.line, char: pos.character,
    });
    if (!result)
        return [];
    return result.map((c) => ({
        label: c.label,
        kind: c.kind,
        detail: c.detail,
        insertText: c.insertText,
    }));
});
connection.onHover(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return null;
    const result = await callBridge("get_hover", {
        text: doc.getText(), line: params.position.line, char: params.position.character,
    });
    if (!result)
        return null;
    return { contents: { kind: "markdown", value: `**${result.detail}**  \n${result.text}` } };
});
connection.onDocumentSymbol(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return [];
    const result = await callBridge("get_symbols", { text: doc.getText() });
    if (!result)
        return [];
    return result.map((s) => ({
        name: s.name,
        kind: s.kind,
        detail: s.detail,
        range: { start: { line: s.line, character: 0 }, end: { line: s.line, character: 1000 } },
        selectionRange: { start: { line: s.line, character: 0 }, end: { line: s.line, character: 1000 } },
    }));
});
connection.onDefinition(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return null;
    const result = await callBridge("get_definition", {
        text: doc.getText(), line: params.position.line, char: params.position.character,
    });
    if (!result)
        return null;
    return {
        uri: params.textDocument.uri,
        range: {
            start: { line: result.line, character: result.char },
            end: { line: result.line, character: result.char + 1 },
        },
    };
});
connection.onDocumentFormatting(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return null;
    const result = await callBridge("get_format", { text: doc.getText() });
    if (!result || typeof result !== "string")
        return null;
    return [{ range: { start: { line: 0, character: 0 }, end: { line: 99999, character: 0 } }, newText: result }];
});
connection.onSignatureHelp(async (params) => {
    const doc = documents.get(params.textDocument.uri);
    if (!doc)
        return null;
    const text = doc.getText();
    const pos = params.position;
    const line = text.split("\n")[pos.line] || "";
    const before = line.slice(0, pos.character);
    if (before.includes("play chord")) {
        return {
            signatures: [{
                    label: "play chord(root, quality) @dur:q @vel:mf",
                    documentation: "Play a chord. quality: major, minor, dom7, min7, Maj7, dim, aug, sus4, sus2",
                    parameters: [
                        { label: "root", documentation: "Chord root note (C, D#, F, ...)" },
                        { label: "quality", documentation: "major, minor, dom7, min7, Maj7, dim, aug, sus4, sus2" },
                    ],
                }],
            activeParameter: before.endsWith(", ") ? 1 : 0,
            activeSignature: 0,
        };
    }
    if (before.includes("play note")) {
        return {
            signatures: [{
                    label: "play note(note) @dur:q @vel:mf",
                    documentation: "Play a single note. note: C4, D#5, Bb3...",
                    parameters: [{ label: "note", documentation: "Note name + octave (C4, E5, Bb3)" }],
                }],
            activeParameter: 0,
            activeSignature: 0,
        };
    }
    return null;
});
documents.listen(connection);
connection.onRequest("hellforge/bridgeRequest", async (params) => {
    const { method, params: p } = params || {};
    if (!method)
        return { ok: false, error: "no method" };
    return await callBridge(method, p || {});
});
connection.listen();
