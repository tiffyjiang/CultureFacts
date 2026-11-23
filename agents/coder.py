"""Coder agent: generates application code from the Analyst's spec."""

import json

from agents.base import Agent
from mcp_client.client import MCPClient

# Placeholder code so the pipeline runs before the real LLM is wired in
_STUB_CODE = '''"""Culture Facts (placeholder from the stub Coder agent)."""

FACTS = {
    "Japan": ["Bowing is a common greeting."],
    "Mexico": ["Dia de los Muertos honors loved ones who have died."],
}


def get_countries():
    """Return countries that have facts."""
    return sorted(FACTS)


def get_facts(country):
    """Return facts for a country, or [] if unknown."""
    return FACTS.get(country, [])
'''


class CoderAgent(Agent):
    """Writes the generated code to the workspace via MCP."""

    name = "coder"
    role = "Generates runnable application code from the spec"
    output_type = "code_ready"

    async def process(self, content: str, mcp: MCPClient) -> str:
        """Stub: write placeholder code. TODO (Agents): generate code with an LLM."""
        spec = json.loads(content)
        module_path = spec.get("module", "app/culture_facts.py")

        await mcp.call_tool("write_file", path="app/__init__.py", content="")
        await mcp.call_tool("write_file", path=module_path, content=_STUB_CODE)

        return json.dumps({"files": [module_path], "spec": spec})