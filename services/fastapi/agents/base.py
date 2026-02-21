"""
Jarvis Control Tower — Base Agent
Abstract base class for all agents in the pipeline.
"""
import time
import logging
from abc import ABC, abstractmethod
from models.schemas import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for Jarvis agents.

    Each agent follows a standard interface:
      input (AgentInput) → run() → output (AgentOutput)

    Subclasses implement `execute()` with their specific logic.
    """

    name: str = "base_agent"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute the agent with timing and error handling.
        Subclasses should override `execute()` instead.
        """
        start = time.time()
        try:
            logger.info("[%s] Starting with input: %s", self.name, agent_input.text[:100])
            result = await self.execute(agent_input)
            duration = (time.time() - start) * 1000
            result.duration_ms = round(duration, 2)
            logger.info("[%s] Completed in %.0fms", self.name, duration)
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error("[%s] Failed after %.0fms: %s", self.name, duration, str(e))
            return AgentOutput(
                agent_name=self.name,
                success=False,
                error=str(e),
                duration_ms=round(duration, 2),
            )

    @abstractmethod
    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Implement the agent's core logic. Must be overridden by subclasses."""
        ...
