"""
MCP server for Culture Facts: exposes tools agents use to save files,
run tests, and send messages to each other. File access is limited to ./workspace.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / "workspace"               # generated code + tests
LOG_FILE = PROJECT_ROOT / "logs" / "messages.jsonl"  # agent messages, for the demo

WORKSPACE.mkdir(exist_ok=True)
LOG_FILE.parent.mkdir(exist_ok=True)

# Server instance; tools are registered with @mcp.tool()
mcp = FastMCP("culture-facts", log_level="WARNING")

# In-memory message board for one pipeline run (server lives for one run)
_messages: list[dict] = []

# Helpers (not exposed as tools)
def _safe_path(relative_path: str) -> Path:
    """Resolve a path inside WORKSPACE; reject anything outside it (guardrail)."""
    path = (WORKSPACE / relative_path).resolve()
    if not path.is_relative_to(WORKSPACE.resolve()):
        raise ValueError(f"Path '{relative_path}' is outside the workspace")
    return path

def _log(entry: dict) -> None:
    """Append one message to logs/messages.jsonl for the demo."""
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# File tools
@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write text to a workspace file, creating folders as needed."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}"


@mcp.tool()
def read_file(path: str) -> str:
    """Read a text file from the workspace."""
    return _safe_path(path).read_text(encoding="utf-8")


@mcp.tool()
def list_files() -> list[str]:
    """List all files in the workspace as relative paths."""
    return sorted(
        str(p.relative_to(WORKSPACE))
        for p in WORKSPACE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != ".gitkeep"
    )


@mcp.tool()
def reset_workspace() -> str:
    """Delete all generated files before a new run."""
    for item in WORKSPACE.iterdir():
        if item.name == ".gitkeep":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    _messages.clear()
    return "Workspace reset"

# Test tool
@mcp.tool()
def run_tests(test_path: str = "tests") -> dict:
    """Run pytest on generated tests; return pass/fail counts and output."""
    target = _safe_path(test_path)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=120,                                        # guardrail: no infinite loops
        env={**os.environ, "PYTHONPATH": str(WORKSPACE)},   # lets tests `import app...`
    )
    output = proc.stdout + proc.stderr

    # Parse pytest's summary line, e.g. "8 passed, 2 failed in 0.12s"
    counts = {"passed": 0, "failed": 0, "error": 0}
    for number, word in re.findall(r"(\d+) (passed|failed|errors?)", output):
        counts["error" if word.startswith("error") else word] += int(number)

    return {
        **counts,
        "total": sum(counts.values()),
        "exit_code": proc.returncode,
        "output": output[-4000:],  # tail only, keeps responses small
    }

# Messaging tools: how agents hand work to each other over MCP
@mcp.tool()
def send_message(sender: str, recipient: str, msg_type: str, content: str) -> dict:
    """Post a message from one agent to another (format in docs/interfaces.md)."""
    message = {
        "id": len(_messages) + 1,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "content": content,
    }
    _messages.append(message)
    _log(message)
    return message

@mcp.tool()
def read_messages(recipient: str) -> list[dict]:
    """Return all messages addressed to an agent, oldest first."""
    return [m for m in _messages if m["recipient"] == recipient]

if __name__ == "__main__":
    mcp.run()  # stdio transport