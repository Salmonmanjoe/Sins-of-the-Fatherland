#!/usr/bin/env python3
"""AI OS entry point."""
import os
import sys

def check_env():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set — ARIA AI features will fail.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-...")
        print()

def main():
    check_env()
    from ai_os.ui.desktop import Desktop
    app = Desktop()
    app.run()

if __name__ == "__main__":
    # Make sure imports work when run directly from ai_os/
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    main()
