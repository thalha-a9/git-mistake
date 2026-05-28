"""
display.py - All terminal output, colors, and formatting for GitMistake
"""

# ── ANSI color codes ────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
PURPLE = "\033[95m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

SEVERITY_COLOR = {
    "low":    GREEN,
    "medium": YELLOW,
    "high":   RED,
}

SEVERITY_ICON = {
    "low":    "🟢",
    "medium": "🟡",
    "high":   "🔴",
}

BANNER = f"""
{RED}{BOLD}
  ██████╗ ██╗████████╗    ███╗   ███╗██╗███████╗████████╗ █████╗ ██╗  ██╗███████╗
 ██╔════╝ ██║╚══██╔══╝    ████╗ ████║██║██╔════╝╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝
 ██║  ███╗██║   ██║       ██╔████╔██║██║███████╗   ██║   ███████║█████╔╝ █████╗  
 ██║   ██║██║   ██║       ██║╚██╔╝██║██║╚════██║   ██║   ██╔══██║██╔═██╗ ██╔══╝  
 ╚██████╔╝██║   ██║       ██║ ╚═╝ ██║██║███████║   ██║   ██║  ██║██║  ██╗███████╗
  ╚═════╝ ╚═╝   ╚═╝       ╚═╝     ╚═╝╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
{RESET}{CYAN}  v1.0.0 · AI-powered Git disaster recovery · https://github.com/yourname/git-mistake{RESET}
{DIM}  ─────────────────────────────────────────────────────────────────────────────{RESET}
"""


def print_banner():
    print(BANNER)


def print_thinking(msg: str):
    print(f"  {CYAN}⟳  {msg}{RESET}", flush=True)


def print_error(msg: str):
    print(f"\n  {RED}{BOLD}✗  {msg}{RESET}\n")


def print_fix(result: dict):
    severity = result.get("severity", "medium")
    color    = SEVERITY_COLOR.get(severity, YELLOW)
    icon     = SEVERITY_ICON.get(severity, "🟡")

    # ── Diagnosis header ──────────────────────────────────────────────
    print(f"\n  {color}{BOLD}{icon}  DIAGNOSIS:{RESET}  {BOLD}{result.get('diagnosis', 'Unknown issue')}{RESET}")
    print(f"  {DIM}{'─' * 70}{RESET}")

    # ── Explanation ───────────────────────────────────────────────────
    print(f"\n  {BLUE}📋  WHAT HAPPENED{RESET}")
    explanation = result.get("explanation", "")
    # Wrap explanation at ~68 chars
    words = explanation.split()
    line = "     "
    for word in words:
        if len(line) + len(word) > 72:
            print(line)
            line = "     " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    # ── Fix steps ─────────────────────────────────────────────────────
    print(f"\n  {GREEN}{BOLD}🔧  HOW TO FIX IT{RESET}\n")
    for step in result.get("steps", []):
        if not step:
            print()
        elif step.startswith("#"):
            print(f"  {DIM}{CYAN}{step}{RESET}")
        else:
            print(f"  {BOLD}{WHITE}  $ {step}{RESET}")

    # ── Safety reminder ───────────────────────────────────────────────
    print(f"\n  {DIM}{'─' * 70}{RESET}")
    print(f"  {YELLOW}💾  Safety tip: create a backup branch before running destructive commands{RESET}")
    print(f"  {DIM}     $ git branch backup-$(date +%s){RESET}\n")


def print_context(ctx: dict):
    print(f"\n  {CYAN}{BOLD}🔍  GIT CONTEXT{RESET}\n")
    labels = {
        "branch":               "Current Branch",
        "status":               "Status",
        "recent_commits":       "Recent Commits",
        "reflog":               "Reflog",
        "stash":                "Stash",
        "merge_in_progress":    "Merge In Progress",
        "rebase_in_progress":   "Rebase In Progress",
        "cherry_pick_in_progress": "Cherry-pick In Progress",
    }
    for key, label in labels.items():
        val = ctx.get(key, "")
        if not val and val is not True:
            continue
        print(f"  {CYAN}{label}:{RESET}")
        for line in str(val).split("\n"):
            print(f"    {DIM}{line}{RESET}")
        print()
