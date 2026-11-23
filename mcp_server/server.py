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


if __name__ == "__main__":
    mcp.run()  # stdio transport