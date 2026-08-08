import * as vscode from "vscode";
import * as path from "path";

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

async function pickVersion(title: string): Promise<string | undefined> {
  const pick = await vscode.window.showQuickPick(VERSIONS, {
    placeHolder: "Choose the syntax version",
    title,
  });
  return pick?.label;
}

async function openOutput(result: any, doneLabel: string): Promise<void> {
  const out = result?.output;
  if (out) {
    try {
      await vscode.workspace.fs.stat(vscode.Uri.file(out));
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(out));
      await vscode.window.showTextDocument(doc, { preview: false });
      vscode.window.showInformationMessage(`${doneLabel}: ${path.basename(out)}`);
      return;
    } catch {
      /* fall through to generic message */
    }
  }
  if (result?.ok === false) {
    vscode.window.showErrorMessage(`Conversion failed: ${result.error || "unknown error"}`);
  } else {
    vscode.window.showInformationMessage(`${doneLabel} — output written next to source.`);
  }
}

export async function convertActiveFile(sendRequest: (m: string, p: any) => Promise<any>) {
  const editor = vscode.window.activeTextEditor;
  const file = editor?.document.uri.fsPath;
  if (!file) {
    vscode.window.showErrorMessage("Open an .e/.ei/.eic file to convert it.");
    return;
  }

  const mode = await vscode.window.showQuickPick(
    [
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
    ],
    { placeHolder: "Convert to what?", title: "HELLFORGE Convert" },
  );
  if (!mode) return;

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: `Converting…` },
    async () => {
      if (mode.value === "midi") {
        const result = await sendRequest("export_midi", { path: file });
        await openOutput(result, "MIDI exported");
        return;
      }

      const target = await pickVersion(
        mode.value === "eic" ? "Convert to .eic — syntax version" : "Convert Syntax — target version",
      );
      if (!target) return;

      if (mode.value === "eic") {
        const result = await sendRequest("convert_to_eic", { path: file, target });
        await openOutput(result, `Converted to .eic (${target})`);
      } else {
        const result = await sendRequest("convert_syntax", { path: file, target });
        await openOutput(result, `Converted to ${target}`);
      }
    },
  );
}
