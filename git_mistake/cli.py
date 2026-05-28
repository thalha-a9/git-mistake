#!/usr/bin/env python3
"""
GitMistake - AI-powered Git disaster recovery
"""

import sys
import argparse
from .context import get_git_context, is_git_repo
from .detector import diagnose_locally
from .ai_helper import call_claude_api
from .display import print_banner, print_fix, print_error, print_context, print_thinking

def main():
    parser = argparse.ArgumentParser(
        prog="git-mistake",
        description="GitMistake — AI-powered Git disaster recovery",
        epilog='Example: git-mistake "I accidentally ran git reset --hard and lost my commits"'
    )
    parser.add_argument("problem", nargs="?", help="Describe your git problem in plain English")
    parser.add_argument("--no-ai", action="store_true", help="Pattern matching only, no AI call")
    parser.add_argument("--context", action="store_true", help="Print current git context and exit")
    parser.add_argument("--version", action="version", version="git-mistake 1.0.1")

    args = parser.parse_args()
    print_banner()

    if not is_git_repo():
        print_error("Not inside a Git repository. Navigate to your project first.")
        sys.exit(1)

    print_thinking("Scanning your git state...")
    context = get_git_context()

    if args.context:
        print_context(context)
        return

    problem = args.problem
    if not problem:
        print("\033[93mDescribe your git problem:\033[0m ", end="", flush=True)
        problem = input().strip()
        if not problem:
            print_error("No problem described. Run: git-mistake 'your problem here'")
            sys.exit(1)

    print_thinking("Diagnosing...")

    # Try fast local pattern match first
    fix = diagnose_locally(context, problem)

    # Fall back to AI for complex/unknown issues
    if not fix and not args.no_ai:
        print_thinking("Consulting AI for deeper analysis...")
        fix = call_claude_api(context, problem)

    if fix:
        print_fix(fix)
    else:
        print_error(
            "Couldn't auto-diagnose. Try running: git reflog\n"
            "  Then open an issue at: https://github.com/thalha-a9/git-mistake/issues"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
