"""
Base class for all agents. Each turn goes through MCP: read inbox ->
process (the LLM call goes here) -> send result to the next agent.
"""

from abc import ABC, abstractmethod

from mcp_client.client import MCPClient


class Agent(ABC):
    """Shared behavior for the Analyst, Coder and Tester agents."""

    name: str = "agent"          # used as sender/recipient in messages
    role: str = ""               # one-line description for the demo/report
    output_type: str = "result"  # msg_type this agent sends when done

    def __init__(self, next_agent: str):
        """Set who receives this agent's output (another agent or "orchestrator")."""
        self.next_agent = next_agent

    async def step(self, mcp: MCPClient) -> dict:
        """One turn: read the latest message, process it, send the result onward."""
        inbox = await mcp.call_tool("read_messages", recipient=self.name)
        if not inbox:
            raise RuntimeError(f"{self.name} has no messages to work on")

        content = await self.process(inbox[-1]["content"], mcp)

        return await mcp.call_tool(
            "send_message",
            sender=self.name,
            recipient=self.next_agent,
            msg_type=self.output_type,
            content=content,
        )

    @abstractmethod
    async def process(self, content: str, mcp: MCPClient) -> str:
        """Do this agent's job on the incoming content; return the outgoing content."""