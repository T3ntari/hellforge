"""Configuration, color constants, and paths for the E Language AI Agent."""

import os
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTAX_PATH = os.path.join(PROJECT_DIR, "SYNTAX.md")
GENERATED_DIR = os.path.join(PROJECT_DIR, "ai_generated")
EP_PATH = os.path.join(PROJECT_DIR, "ep.py")
OLLAMA_HOST = "http://localhost:11434"
PROJECTS_FILE = os.path.join(GENERATED_DIR, ".projects.json")
SESSION_FILE = os.path.join(GENERATED_DIR, ".session.json")
SESSION_INDEX = os.path.join(GENERATED_DIR, ".sessions_index.json")
MAX_TOKENS = 32000

os.makedirs(GENERATED_DIR, exist_ok=True)

# Terminal colors
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
GREY = "\033[90m"


def c(text, color=""):
    return f"{color}{text}{R}" if color and sys.stdout.isatty() else text


def print_thinking(text):
    for line in text.strip().split("\n"):
        if line.strip():
            print(f"  {c(line, GREY)}")


# Shared state (imported by other modules)
CURRENT_PROJECT = None
DELETE_PERM = "prompt"
MODEL = None
CONVERSATION = []
TOKEN_ESTIMATE = 0
SAVED_PLAN = ""
VERSIONS = {}
