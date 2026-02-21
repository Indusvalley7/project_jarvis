"""Tests for the base agent framework."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput


class DummyAgent(BaseAgent):
    """A test agent that returns a fixed response."""
    name = "dummy_agent"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={"echo": agent_input.text},
        )


class FailingAgent(BaseAgent):
    """A test agent that always raises an error."""
    name = "failing_agent"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        raise ValueError("Something went wrong")


@pytest.mark.asyncio
class TestBaseAgent:
    async def test_successful_run(self):
        agent = DummyAgent()
        inp = AgentInput(user_id="u1", text="hello world")
        result = await agent.run(inp)

        assert result.success is True
        assert result.agent_name == "dummy_agent"
        assert result.data["echo"] == "hello world"
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    async def test_failed_run_returns_error(self):
        agent = FailingAgent()
        inp = AgentInput(user_id="u1", text="trigger failure")
        result = await agent.run(inp)

        assert result.success is False
        assert result.agent_name == "failing_agent"
        assert "Something went wrong" in result.error
        assert result.duration_ms >= 0
