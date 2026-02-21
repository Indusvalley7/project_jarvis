"""
Jarvis Control Tower — Classifier Agent
Classifies user intent from natural language input.
"""
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput, Intent
from services.ollama_client import ollama_client


CLASSIFIER_SYSTEM = """You are an intent classifier for a personal AI assistant called Jarvis.
Your job is to classify the user's message into exactly one intent category.

Available intents:
- reminder: Setting reminders, alarms, or time-based notifications
- note: Saving notes, bookmarks, or text snippets
- question: Asking a question that needs an answer
- memory_update: Updating personal information, preferences, or facts about the user
- diagnostic: System health checks, debugging, or status inquiries
- unknown: Anything that doesn't fit the above categories

You MUST respond with ONLY a valid JSON object, nothing else:
{"intent": "<intent>", "clean_text": "<cleaned version of the message>", "confidence": <0.0-1.0>}"""


class ClassifierAgent(BaseAgent):
    """Classifies user messages into intent categories."""

    name = "classifier"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        prompt = f"Classify this message:\n\n{agent_input.text}"

        result = await ollama_client.generate_json(prompt, system=CLASSIFIER_SYSTEM)

        # Extract intent, defaulting to unknown
        intent_str = result.get("intent", "unknown").lower()
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.UNKNOWN

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "intent": intent.value,
                "clean_text": result.get("clean_text", agent_input.text),
                "confidence": result.get("confidence", 0.5),
            },
        )


classifier_agent = ClassifierAgent()
