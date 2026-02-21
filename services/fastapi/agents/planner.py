"""
Jarvis Control Tower — Planner Agent
Decomposes classified intents into executable action plans.
"""
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput
from services.ollama_client import ollama_client


PLANNER_SYSTEM = """You are a task planner for a personal AI assistant called Jarvis.
Given a user's message and its classified intent, create a step-by-step action plan.

Available tools you can plan to use:
- memory_search: Search past conversations or knowledge base
- memory_store: Save information to long-term memory
- n8n_trigger: Trigger an n8n workflow (for reminders, notifications, etc.)
- llm_generate: Generate a text response using the LLM
- n8n_health_check: Check system health

Respond with ONLY a valid JSON object:
{
  "steps": [
    {"action": "<tool_name>", "params": {"key": "value"}, "reason": "<why this step>"}
  ],
  "summary": "<brief plan summary>"
}"""


class PlannerAgent(BaseAgent):
    """Creates action plans based on classified intent."""

    name = "planner"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        context_str = ""
        if agent_input.context:
            context_str = f"\n\nRelevant context from memory:\n" + "\n".join(
                f"- {c}" for c in agent_input.context
            )

        prompt = f"""Intent: {agent_input.intent}
User message: {agent_input.text}{context_str}

Create an action plan for this request."""

        result = await ollama_client.generate_json(prompt, system=PLANNER_SYSTEM)

        steps = result.get("steps", [])
        if not steps:
            # Fallback: simple plan based on intent
            steps = self._fallback_plan(agent_input)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "steps": steps,
                "summary": result.get("summary", "Fallback plan generated"),
            },
        )

    def _fallback_plan(self, agent_input: AgentInput) -> list[dict]:
        """Generate a deterministic fallback plan based on intent."""
        intent = agent_input.intent

        if intent == "reminder":
            return [
                {"action": "n8n_trigger", "params": {"workflow": "reminder", "text": agent_input.text}, "reason": "Schedule reminder via n8n"},
                {"action": "memory_store", "params": {"text": agent_input.text}, "reason": "Save reminder to memory"},
                {"action": "llm_generate", "params": {"task": "confirm"}, "reason": "Generate confirmation"},
            ]
        elif intent == "note":
            return [
                {"action": "memory_store", "params": {"text": agent_input.text}, "reason": "Save note to knowledge base"},
                {"action": "llm_generate", "params": {"task": "confirm"}, "reason": "Confirm note saved"},
            ]
        elif intent == "question":
            return [
                {"action": "memory_search", "params": {"query": agent_input.text}, "reason": "Search for relevant context"},
                {"action": "llm_generate", "params": {"task": "answer"}, "reason": "Generate answer with context"},
            ]
        elif intent == "memory_update":
            return [
                {"action": "memory_store", "params": {"text": agent_input.text}, "reason": "Update user memory"},
                {"action": "llm_generate", "params": {"task": "confirm"}, "reason": "Confirm update"},
            ]
        elif intent == "diagnostic":
            return [
                {"action": "n8n_health_check", "params": {}, "reason": "Check system health"},
                {"action": "llm_generate", "params": {"task": "report"}, "reason": "Generate health report"},
            ]
        else:
            return [
                {"action": "llm_generate", "params": {"task": "respond"}, "reason": "Generate general response"},
            ]


planner_agent = PlannerAgent()
