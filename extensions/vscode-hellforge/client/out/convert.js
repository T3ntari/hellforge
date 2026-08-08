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
exports.convertActiveFile = convertActiveFile;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
/**
 * HELLFORGE Convert GUI — three conversion modes:
 *   1. Convert to MIDI        (no version picker)
 *   2. Convert to .eic        (version picker: v1–v4)
 *   3. Convert Syntax         (version picker: v1–v4)
 */
const VERSIONS = [
    { label: "v4", description: "Current standard — math, polyrhythms, punctuation" },
    { label: "v3", description: "Extended — macros, shorthand, repeats" },
    { label: "v2", description: "Semantic mode" },
    { label: "v1", description: "Legacy machine/human" },
];
async function pickVersion(title) {
    const pick = await vscode.window.showQuickPick(VERSIONS, {
        placeHolder: "Choose the syntax version",
        title,
    });
    return pick?.label;
}
async function openOutput(result, doneLabel) {
    const out = result?.output;
    if (out) {
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(out));
            const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(out));
            await vscode.window.showTextDocument(doc, { preview: false });
            vscode.window.showInformationMessage(`${doneLabel}: ${path.basename(out)}`);
            return;
        }
        catch {
            /* fall through to generic message */
        }
    }
    if (result?.ok === false) {
        vscode.window.showErrorMessage(`Conversion failed: ${result.error || "unknown error"}`);
    }
    else {
        vscode.window.showInformationMessage(`${doneLabel} — output written next to source.`);
    }
}
async function convertActiveFile(sendRequest) {
    const editor = vscode.window.activeTextEditor;
    const file = editor?.document.uri.fsPath;
    if (!file) {
        vscode.window.showErrorMessage("Open an .e/.ei/.eic file to convert it.");
        return;
    }
    const mode = await vscode.window.showQuickPick([
        {
            label: "$(file-binary) Convert to MIDI",
            description: "Compile to .mid",
            detail: "Exports the audio output — no version picker",
            value: "midi",
        },
        {
            label: "$(file-zip) Convert to .eic",
            description: "E Index Clear bundle",
            detail: "Choose a syntax version, wraps into a project bundle",
            value: "eic",
        },
        {
            label: "$(arrow-swap) Convert Syntax",
            description: "v1 / v2 / v3 / v4",
            detail: "Rewrite the source in another syntax version",
            value: "syntax",
        },
    ], { placeHolder: "Convert to what?", title: "HELLFORGE Convert" });
    if (!mode)
        return;
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: `Converting…` }, async () => {
        if (mode.value === "midi") {
            const result = await sendRequest("export_midi", { path: file });
            await openOutput(result, "MIDI exported");
            return;
        }
        const target = await pickVersion(mode.value === "eic" ? "Convert to .eic — syntax version" : "Convert Syntax — target version");
        if (!target)
            return;
        if (mode.value === "eic") {
            const result = await sendRequest("convert_to_eic", { path: file, target });
            await openOutput(result, `Converted to .eic (${target})`);
        }
        else {
            const result = await sendRequest("convert_syntax", { path: file, target });
            await openOutput(result, `Converted to ${target}`);
        }
    });
}
