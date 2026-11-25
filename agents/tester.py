"""Tester agent: generates pytest tests for the Coder's output."""

import json

from agents.base import Agent
from mcp_client.client import MCPClient

# Placeholder tests so the pipeline runs before the real LLM is wired in
_STUB_TESTS = '''"""Tests for Culture Facts (placeholder from the stub Tester agent)."""

from app.culture_facts import get_countries, get_facts


def test_countries_not_empty():
    assert len(get_countries()) > 0


def test_known_country_has_facts():
    assert get_facts("Japan")


def test_unknown_country_returns_empty_list():
    assert get_facts("Atlantis") == []
'''


class TesterAgent(Agent):
    """Writes test files to the workspace via MCP."""

    name = "tester"
    role = "Generates pytest test cases for the generated code"
    output_type = "tests_ready"

    async def process(self, content: str, mcp: MCPClient) -> str:
        """Stub: write placeholder tests. TODO (Agents/Testing): generate 10+ tests with an LLM."""
        info = json.loads(content)
        code = await mcp.call_tool("read_file", path=info["files"][0])  # real agent puts this in the prompt
        _ = code

        test_path = "tests/test_culture_facts.py"
        await mcp.call_tool("write_file", path=test_path, content=_STUB_TESTS)
        return json.dumps({"test_files": [test_path]})