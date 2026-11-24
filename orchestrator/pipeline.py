"""
Orchestrator: runs the full pipeline. Every handoff is an MCP message:
requirements -> Analyst -> Coder -> Tester -> run_tests
The GUI should call run_pipeline(requirements_text) and display the result.
"""

from agents.analyst import AnalystAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from mcp_client.client import MCPClient

AGENT_NAMES = ["analyst", "coder", "tester", "orchestrator"]


async def run_pipeline(requirements: str) -> dict:
    """Run every agent in order; return tools, messages, files and test results."""
    agents = [
        AnalystAgent(next_agent="coder"),
        CoderAgent(next_agent="tester"),
        TesterAgent(next_agent="orchestrator"),
    ]

    async with MCPClient() as mcp:
        await mcp.call_tool("reset_workspace")

        # Kick off: send the requirements to the first agent
        await mcp.call_tool(
            "send_message",
            sender="orchestrator",
            recipient=agents[0].name,
            msg_type="requirements",
            content=requirements,
        )

        # Each agent reads its inbox and hands off to the next via MCP
        for agent in agents:
            print(f"[orchestrator] running {agent.name}: {agent.role}")
            await agent.step(mcp)

        # Collect every message for the GUI/demo, in send order
        messages = []
        for name in AGENT_NAMES:
            messages += await mcp.call_tool("read_messages", recipient=name)

        return {
            "tools": mcp.tool_names,
            "messages": sorted(messages, key=lambda m: m["id"]),
            "files": await mcp.call_tool("list_files"),
            "test_results": await mcp.call_tool("run_tests"),
        }