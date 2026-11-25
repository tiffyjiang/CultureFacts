"""Requirements Analyst agent: turns raw requirements into a structured spec."""

import json

from agents.base import Agent
from mcp_client.client import MCPClient


class AnalystAgent(Agent):
    """Converts requirement text into a JSON spec for the Coder."""

    name = "analyst"
    role = "Turns raw functional requirements into a structured spec"
    output_type = "spec"

    async def process(self, content: str, mcp: MCPClient) -> str:
        """Stub: pull '-' bullet lines as features. TODO (Agents): replace with LLM call."""
        features = [
            line.strip().lstrip("- ").strip()
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        spec = {"app_name": "Culture Facts", "module": "app/culture_facts.py", "features": features}
        return json.dumps(spec)