#!/usr/bin/env python3
"""
E Language AI Agent — CLI entry point.
Refactored into ai/ package. This file is a forwarder.

Usage:
    python ai.py
    python ai.py --list-models
"""

import sys
import os

# Ensure package directory is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.cli import main

if __name__ == "__main__":
    main()
