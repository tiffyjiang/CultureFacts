"""
Command-line entry point: runs the pipeline once and prints a summary.
Usage: python main.py [path/to/requirements.md]
"""

import asyncio
import sys
from pathlib import Path

from orchestrator.pipeline import run_pipeline

DEFAULT_REQUIREMENTS = Path(__file__).parent / "requirements" / "culture_facts.md"


def main() -> None:
    """Load requirements, run the pipeline, and print the results."""
    req_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REQUIREMENTS
    results = asyncio.run(run_pipeline(req_file.read_text(encoding="utf-8")))

    print("\nMCP tools discovered:", ", ".join(results["tools"]))

    print("\nAgent messages (via MCP):")
    for m in results["messages"]:
        print(f"  #{m['id']} {m['sender']} -> {m['recipient']} [{m['type']}]")

    print("\nGenerated files:", ", ".join(results["files"]))

    t = results["test_results"]
    print(f"\nTests: {t['passed']} passed, {t['failed']} failed, {t['error']} errors (total {t['total']})")


if __name__ == "__main__":
    main()