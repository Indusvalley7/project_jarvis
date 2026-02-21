"""
Jarvis Control Tower — Critic Agent
Validates executor output for quality and completeness.
"""
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput
from services.ollama_client import ollama_client


CRITIC_SYSTEM = """You are a quality checker for an AI assistant called Jarvis.
Your job is to evaluate whether a response is good enough to send to the user.

Evaluate on these criteria:
1. Relevance: Does it address the user's request?
2. Completeness: Is the response complete or missing something?
3. Clarity: Is it clear and well-structured?
4. Accuracy: Does it seem factually reasonable?

Respond with ONLY a valid JSON object:
{"pass": true/false, "score": <1-10>, "feedback": "<brief feedback>"}"""


class CriticAgent(BaseAgent):
    """Validates the quality of executor output."""

    name = "critic"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        response = agent_input.metadata.get("executor_response", "")
        original_text = agent_input.text

        prompt = f"""Original user request: {original_text}
Intent: {agent_input.intent}

Generated response to evaluate:
{response}

Is this response good enough to send to the user?"""

        result = await ollama_client.generate_json(prompt, system=CRITIC_SYSTEM)

        passed = result.get("pass", True)
        score = result.get("score", 7)
        feedback = result.get("feedback", "No feedback")

        # If score < 4, mark as failed
        if isinstance(score, (int, float)) and score < 4:
            passed = False

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "pass": passed,
                "score": score,
                "feedback": feedback,
                "response": response,
            },
        )


critic_agent = CriticAgent()
