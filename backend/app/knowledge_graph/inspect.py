import sys
import io
from app.knowledge_graph.graph_engine import denial_kg

# Ensure utf-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_code_subgraph(code_str: str):
    subgraph = denial_kg.get_subgraph(code_str)
    if not subgraph:
        print(f"\n{RED}[ERROR] CARC Denial Code '{code_str}' not found in Knowledge Graph.{RESET}")
        overview = denial_kg.get_overview()
        print(f"{YELLOW}Available codes:{RESET} {', '.join(overview['carc_codes'])}")
        return

    print("=" * 85)
    print(f"{BOLD}{CYAN}NOVAARC RCM — DENIAL KNOWLEDGE GRAPH INSPECTOR{RESET}")
    print(f"{BOLD}CARC CODE:{RESET} {YELLOW}{subgraph.code}{RESET} — {subgraph.code_description}")
    print(f"{BOLD}CATEGORY:{RESET}  {BLUE}{subgraph.category}{RESET}")
    print(f"{BOLD}SUBGRAPH METRICS:{RESET} {len(subgraph.nodes)} Connected Nodes | {len(subgraph.edges)} Relational Edges")
    print("=" * 85)

    for i, sc in enumerate(subgraph.scenarios, 1):
        print(f"\n{BOLD}{GREEN}├── [SCENARIO {i}] {sc['title']}{RESET}")
        print(f"│   {DIM}Root Cause:{RESET} {sc.get('root_cause')}")

        # Investigation
        inv_steps = sc.get("investigation_steps", [])
        if inv_steps:
            print(f"│   {BOLD}{YELLOW}▼ INVESTIGATION CHECKLIST:{RESET}")
            for step in inv_steps:
                print(f"│     • {step}")

        # Forms & Box Requirements
        form = sc.get("form_requirements", {})
        if form:
            print(f"│   {BOLD}{MAGENTA}▼ FORM & BOX REQUIREMENTS:{RESET}")
            print(f"│     • Form: {form.get('form_name')} | Box/Segment: {form.get('box_number')}")
            if form.get("required_documents"):
                print(f"│     • Required Attachments: {', '.join(form.get('required_documents'))}")

        # Payer Call Script
        script = sc.get("call_script", {})
        if script:
            print(f"│   {BOLD}{CYAN}▼ PAYER CALL SCRIPT QUESTIONS:{RESET}")
            for k, q in script.items():
                print(f"│     [{k.upper()}]: \"{q}\"")

        # Action Plan
        action_steps = sc.get("action_plan", [])
        if action_steps:
            print(f"│   {BOLD}{GREEN}▼ STEP-BY-STEP RESOLUTION PLAYBOOK:{RESET}")
            for step in action_steps:
                print(f"│     ✓ {step}")

        # Standard AR Call Notes
        notes = sc.get("standard_notes", "")
        if notes:
            print(f"│   {BOLD}▼ STANDARDIZED PRE-FORMATTED AR CALL NOTES:{RESET}")
            print(f"│     {DIM}{notes}{RESET}")

    print("\n" + "=" * 85 + "\n")


def print_overview():
    overview = denial_kg.get_overview()
    print("=" * 85)
    print(f"{BOLD}{CYAN}NOVAARC RCM — KNOWLEDGE GRAPH OVERVIEW{RESET}")
    print(f"Total Nodes: {overview['total_nodes']} | Total Edges: {overview['total_edges']}")
    print("-" * 85)
    print(f"{BOLD}Categories:{RESET}")
    for cat in overview["categories"]:
        print(f"  • {BOLD}{cat['id']}{RESET}: {cat['name']} ({cat['description']})")
    print(f"\n{BOLD}Configured Denial CARC Codes:{RESET}")
    print("  " + ", ".join(overview["carc_codes"]))
    print("=" * 85)
    print(f"{DIM}Usage: python -m app.knowledge_graph.inspect <DENIAL_CODE> (e.g. CO-16, CO-197, CO-29){RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        code_arg = sys.argv[1]
        print_code_subgraph(code_arg)
    else:
        print_overview()
