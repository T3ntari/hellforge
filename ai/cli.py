"""CLI entry point — model selection (Ollama local + cloud), session restore."""

import os
import sys

from .config import (
    c, B, D, CYAN, GREEN, YELLOW, RED, PROJECT_DIR,
)
from .ollama import (
    list_ollama_models,
    openai_list_models,
    is_cloud_model,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from .session import load_session
from .agent import agent_loop


def pick_model():
    import ai.config as cfg

    cloud_models = []
    if OPENAI_API_KEY:
        cloud_models = openai_list_models()
    local_models = list_ollama_models()

    all_models = []
    print()
    if cloud_models:
        print(f"  {c('Cloud (API):', CYAN)}")
        for m in cloud_models:
            all_models.append(m)
            print(f"  {c(f'[{len(all_models)}]', D)} {c(m, GREEN)}")
    if local_models:
        print(f"  {c('Local (Ollama):', CYAN)}")
        for m in local_models:
            all_models.append(m)
            print(f"  {c(f'[{len(all_models)}]', D)} {m}")

    if not all_models:
        print(f"  {c('No models available.', RED)}")
        print(f"  Install Ollama: {c('ollama pull qwen2.5-coder:3b', YELLOW)}")
        print(f"  Or set API key: {c('set E_OPENAI_KEY=sk-...', YELLOW)}")
        sys.exit(1)

    while True:
        try:
            c_ = input(f"\n  {c('Model', B)} [{c('1',CYAN)}{c('-',D)}{c(len(all_models),CYAN)}]: ").strip()
            if not c_:
                cfg.MODEL = all_models[0]
                return
            idx = int(c_) - 1
            if 0 <= idx < len(all_models):
                cfg.MODEL = all_models[idx]
                return
        except (ValueError, IndexError):
            pass


def main():
    import ai.config as cfg

    print(f"""
{c('E Language AI Agent', CYAN)}
{c('Piano composition via Ollama + Cloud API', D)}
""")

    parser = __import__('argparse').ArgumentParser()
    parser.add_argument("--model", help="Model name (bypass picker)")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--api-key", help="Set OpenAI-compatible API key for cloud models")
    parser.add_argument("--api-url", help="Set OpenAI-compatible base URL")
    args = parser.parse_args()

    if args.api_key:
        print(f"  Set E_OPENAI_KEY for future sessions, or pass --api-key each time")
        import ai.ollama as oa
        oa.OPENAI_API_KEY = args.api_key
        os.environ["E_OPENAI_KEY"] = args.api_key

    if args.api_url:
        import ai.ollama as oa
        oa.OPENAI_BASE_URL = args.api_url
        os.environ["E_OPENAI_URL"] = args.api_url

    if args.list_models:
        print(f"\n  {c('Local (Ollama):', CYAN)}")
        for m in list_ollama_models():
            print(f"    {m}")
        if OPENAI_API_KEY:
            print(f"\n  {c('Cloud (API):', CYAN)}")
            for m in openai_list_models():
                print(f"    {m}")
        else:
            print(f"\n  {c('Cloud: set E_OPENAI_KEY or pass --api-key', D)}")
        return

    if args.model:
        cfg.MODEL = args.model
    else:
        pick_model()

    print(f"\n  Model: {c(cfg.MODEL, CYAN)}")
    if is_cloud_model(cfg.MODEL):
        print(f"  API:   {c(OPENAI_BASE_URL, D)}")

    # Session restore
    if load_session():
        n = len(cfg.CONVERSATION)
        proj = os.path.relpath(cfg.CURRENT_PROJECT, PROJECT_DIR) if cfg.CURRENT_PROJECT else "none"
        has_plan = " (plan saved)" if cfg.SAVED_PLAN else ""
        ans = input(f"  > {c(f'Restore session?', YELLOW)} ({n} messages, project: {proj}{has_plan}) [{c('Y',B)}/n] ").strip().lower()
        if ans not in ("", "y", "yes"):
            cfg.CONVERSATION.clear()
            cfg.CURRENT_PROJECT = None
            cfg.SAVED_PLAN = ""
            cfg.TOKEN_ESTIMATE = 0

    try:
        agent_loop()
    except KeyboardInterrupt:
        print(f"\n\n  {c('Bye!', GREEN)}")
    except Exception as e:
        print(f"\n  {c(f'Error: {e}', RED)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
