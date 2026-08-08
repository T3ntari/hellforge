"""Minimal agent — streams cleanly, saves sessions, strips markdown."""

import os
import re
import time

import ai.config as cfg
from .config import (
    c,
    D,
    GREEN,
    YELLOW,
    RED,
    CYAN,
    PROJECT_DIR,
)
from .prompts import build_system_prompt
from .ollama import stream_generate
from .tools import (
    tool_project,
    tool_write,
    tool_compile,
    tool_play,
)
from .session import (
    save_session,
    save_session_snapshot,
    save_project_list,
)


def strip_md(text):
    """Strip markdown formatting — safe for terminal. Leaves backticks for code block detection."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'^###?\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*]\s', '  ', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s', '  ', text, flags=re.MULTILINE)
    return text


def agent_loop():
    section_count = 0
    print(f"  {c('E Agent — describe music, AI builds', D)}\n")

    while True:
        try:
            user = input(f"  {c('>', GREEN)} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.lower() in ("/quit", "/exit"):
            save_project_list()
            save_session()
            break

        if user.lower().startswith("project "):
            from .tools import tool_project as tp
            tp(user[8:].strip())
            save_project_list()
            save_session()
            continue

        if user.lower() == "compile":
            tool_compile()
            continue

        if user.lower() == "play":
            tool_play()
            continue

        # Read with optional line range
        read_match = re.match(r'^read\s+(\S+)(?:\s+(\d+)?(?:\s*-\s*(\d+))?)?$', user, re.I)
        if read_match:
            path = read_match.group(1)
            start = int(read_match.group(2)) if read_match.group(2) else None
            end = int(read_match.group(3)) if read_match.group(3) else None
            if not cfg.CURRENT_PROJECT:
                print(f"  > {c('No project', RED)}")
                continue
            full = os.path.join(cfg.CURRENT_PROJECT, path)
            if not os.path.exists(full):
                print(f"  > {c('Not found:', RED)} {path}")
                continue
            with open(full, "r") as f:
                lines = f.readlines()
            rel = os.path.relpath(full, PROJECT_DIR)
            if start:
                start = max(1, start)
                end = end or start
                end = min(end, len(lines))
                print(f"  > {c(f'{rel} lines {start}-{end}', CYAN)}")
                for i in range(start - 1, end):
                    print(f"    {c(f'{i+1:4d}', D)} {lines[i].rstrip()}")
            else:
                print(f"  > {c(f'{rel} ({len(lines)} lines)', CYAN)}")
                for i, line in enumerate(lines[:20], 1):
                    print(f"    {c(f'{i:4d}', D)} {line.rstrip()}")
                if len(lines) > 20:
                    print(f"    {c(f'... {len(lines)-20} more', D)}")
            continue

        cfg.CONVERSATION.append({"role": "user", "content": user})

        # Build prompt
        prompt_parts = [build_system_prompt()]

        if cfg.SAVED_PLAN and ("build" in user.lower() or "continue" in user.lower()):
            prompt_parts.append(f"""BUILD MODE — generate the next section.

PLAN:
{cfg.SAVED_PLAN[:2000]}

Already written: {section_count} sections.
You can think out loud about the music, then output the E code in a code block.""")

        # Auto-scale max_tokens for large models
        if "deepseek" in (cfg.MODEL or "") or "qwen3" in (cfg.MODEL or ""):
            import ai.ollama as oa
            oa.CLOUD_MAX_TOKENS = 32768

        for msg in cfg.CONVERSATION[-6:]:
            r, c_ = msg["role"], msg["content"]
            if r == "user":
                prompt_parts.append(f"User: {c_[:1000]}")
            elif r == "assistant":
                prompt_parts.append(f"Assistant: {c_[:2000]}")

        prompt_parts.append("Assistant:")
        full = "\n".join(prompt_parts)

        # Stream with real-time output
        print()
        response_text = ""
        in_code = False
        code_buf = ""
        had_code = False

        for typ, data in stream_generate(full):
            if typ == "token":
                response_text += data
                    # Display non-code text immediately
                if not in_code:
                    # Strip markdown for cleaner display
                    data = strip_md(data)
                    # Check for backtick markers in the stream
                    while "```" in data:
                        idx = data.index("```")
                        # Print text before the ```
                        prefix = data[:idx]
                        if prefix:
                            print(prefix, end="", flush=True)
                        # Toggle code mode
                        in_code = not in_code
                        if in_code:
                            code_buf = ""
                        else:
                            if code_buf.strip() and cfg.CURRENT_PROJECT:
                                lines = code_buf.strip().split("\n")
                                machine = [l for l in lines if re.match(r'^[T@]', l.strip())]
                                if machine:
                                    fname = f"parts/part_{int(time.time())}.e"
                                    tool_write(fname, "\n".join(machine))
                                    had_code = True
                                    print(f"  {c('> code saved ->', D)} {c(fname, CYAN)}")
                            code_buf = ""
                        data = data[idx + 3:]
                    if not in_code:
                        print(data, end="", flush=True)
                    else:
                        code_buf += data
                else:
                    # In code block — buffer
                    code_buf += data
                    # Check if closing ``` in this chunk
                    if "```" in code_buf:
                        parts = code_buf.split("```", 1)
                        code_content = parts[0]
                        code_buf = parts[1] if len(parts) > 1 else ""
                        in_code = False
                        if code_content.strip() and cfg.CURRENT_PROJECT:
                            lines = code_content.strip().split("\n")
                            machine = [l for l in lines if re.match(r'^[T@]', l.strip())]
                            if machine:
                                fname = f"parts/part_{int(time.time())}.e"
                                tool_write(fname, "\n".join(machine))
                                had_code = True
                                print(f"  {c('> code saved ->', D)} {c(fname, CYAN)}")

            elif typ == "done":
                response_text = data
            elif typ == "error":
                print(f"\n  {c(f'[Error]', RED)} {data[:200]}")
                break

        print()

        # Also detect raw code outside ``` blocks
        if not had_code and cfg.CURRENT_PROJECT:
            raw = []
            for l in response_text.strip().split("\n"):
                ls = l.strip()
                if re.match(r'^T\d+\s+N\d+', ls) or re.match(r'^@(?:bpm|tempo)', ls, re.I):
                    raw.append(ls)
            if len(raw) >= 2:
                fname = f"parts/part_{int(time.time())}.e"
                tool_write(fname, "\n".join(raw))
                section_count += 1
                had_code = True
                print(f"  {c('>>> code saved to', D)} {c(fname, CYAN)}")

        # Save plan
        wants_plan = user.lower().startswith("/plan") or user.lower().startswith("plan ")
        if wants_plan and len(response_text) > 100:
            cfg.SAVED_PLAN = response_text.strip()
            save_session_snapshot("plan")
            print(f"  > {c('Plan saved', GREEN)}")

        # Auto project creation
        if re.search(r'project\s+(\S+)', response_text, re.I) and not cfg.CURRENT_PROJECT:
            m = re.search(r'project\s+(\S+)', response_text, re.I)
            from .tools import tool_project as tp
            tp(m.group(1))
            save_project_list()

        # Auto compile/play
        if re.search(r'\bcompile\b', response_text, re.I) and cfg.CURRENT_PROJECT:
            tool_compile()
        if re.search(r'\bplay\b', response_text, re.I) and cfg.CURRENT_PROJECT:
            tool_play()

        cfg.CONVERSATION.append({"role": "assistant", "content": response_text})
        save_session()
        tk = len(response_text) // 4
        sections_note = f" | {section_count} sections" if had_code else ""
        print(f"  {c(f'[~{tk}tokens{sections_note}]', D)}")
