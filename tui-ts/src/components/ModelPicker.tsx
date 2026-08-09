import React, { useEffect, useState } from "react";
import { Box, Text, useInput } from "ink";
import type { Color } from "../protocol.js";

const TOKEN_HEX: Record<Color, string> = {
  accent: "#ff4d4d",
  accent2: "#ff8c42",
  text: "#ffebdc",
  dim: "#8c827d",
  ok: "#96c88c",
  err: "#ff6446",
  warn: "#f0be5a",
};

export interface ProviderEntry {
  name: string;
  label: string;
  models: string[];
}

export const PROVIDER_LIST: ProviderEntry[] = [
  {
    name: "openai",
    label: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini"],
  },
  {
    name: "deepseek",
    label: "DeepSeek",
    models: ["deepseek-chat", "deepseek-reasoner", "deepseek-v4"],
  },
  {
    name: "claude",
    label: "Anthropic Claude",
    models: ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
  },
  {
    name: "ollama",
    label: "Ollama (local)",
    models: ["llama3.2", "qwen2.5", "mistral"],
  },
];

export interface ModelPickerProps {
  open: boolean;
  onClose: () => void;
  onPick: (provider: string, model: string) => void;
}

type Pane = "providers" | "models";

export function ModelPicker({ open, onClose, onPick }: ModelPickerProps) {
  const [pane, setPane] = useState<Pane>("providers");
  const [providerIdx, setProviderIdx] = useState(0);
  const [modelIdx, setModelIdx] = useState(0);

  useEffect(() => {
    if (open) {
      setPane("providers");
      setProviderIdx(0);
      setModelIdx(0);
    }
  }, [open]);

  useInput(
    (_input, key) => {
      if (!open) return;
      if (key.escape) {
        onClose();
        return;
      }
      const provider = PROVIDER_LIST[providerIdx];
      if (key.upArrow || key.downArrow) {
        const delta = key.upArrow ? -1 : 1;
        if (pane === "providers") {
          setProviderIdx(
            (providerIdx + delta + PROVIDER_LIST.length) % PROVIDER_LIST.length,
          );
        } else if (provider.models.length > 0) {
          setModelIdx(
            (modelIdx + delta + provider.models.length) % provider.models.length,
          );
        }
        return;
      }
      if (key.leftArrow) {
        setPane("providers");
        return;
      }
      if (key.rightArrow || key.tab) {
        setPane("models");
        return;
      }
      if (key.return) {
        if (pane === "providers") {
          setPane("models");
        } else if (provider.models.length > 0) {
          onPick(provider.name, provider.models[modelIdx]);
        }
      }
    },
    { isActive: open },
  );

  if (!open) return null;

  const provider = PROVIDER_LIST[providerIdx];
  return (
    <Box flexDirection="column" alignItems="center" marginTop={1}>
      <Box
        borderStyle="round"
        borderColor={TOKEN_HEX.accent2}
        flexDirection="column"
        paddingX={2}
        paddingY={1}
        width={64}
      >
        <Text bold color={TOKEN_HEX.accent2}>Model picker</Text>
        <Box flexDirection="row" marginTop={1}>
          <Box flexDirection="column" marginRight={3}>
            <Text dimColor color={TOKEN_HEX.dim}>PROVIDER</Text>
            {PROVIDER_LIST.map((p, i) => {
              const selected = i === providerIdx;
              return (
                <Text
                  key={p.name}
                  color={selected ? TOKEN_HEX.accent : TOKEN_HEX.text}
                  bold={selected}
                >
                  {pane === "providers" && selected ? "▸ " : "  "}{p.label}
                </Text>
              );
            })}
          </Box>
          <Box flexDirection="column">
            <Text dimColor color={TOKEN_HEX.dim}>MODEL</Text>
            {provider.models.map((m, i) => {
              const selected = i === modelIdx;
              return (
                <Text
                  key={m}
                  color={selected ? TOKEN_HEX.accent : TOKEN_HEX.text}
                  bold={selected}
                >
                  {pane === "models" && selected ? "▸ " : "  "}{m}
                </Text>
              );
            })}
          </Box>
        </Box>
        <Text color={TOKEN_HEX.dim} dimColor>
          {"\u2191\u2193"} select · {"\u2190\u2192"} switch pane · Enter pick · Esc close
        </Text>
      </Box>
    </Box>
  );
}
