"""
Jarvis Control Tower — Research Agent
Dedicated agent for Qdrant semantic search and context retrieval.
"""
import logging
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput
from services.qdrant_service import qdrant_service
from config import settings

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Searches Qdrant for relevant context based on the user's query."""

    name = "researcher"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        query = agent_input.text
        user_id = agent_input.user_id

        # Search across multiple collections
        results = {}
        snippets = []

        # 1. Search conversations
        try:
            conv_results = qdrant_service.search(
                collection=settings.COLLECTION_CONVERSATIONS,
                query=query,
                top_k=3,
                filters={"user_id": user_id},
            )
            relevant_convs = [r for r in conv_results if r["score"] > 0.5]
            results["conversations"] = len(relevant_convs)
            snippets.extend([r["text"] for r in relevant_convs])
        except Exception as e:
            logger.warning("Conversation search failed: %s", e)
            results["conversations"] = 0

        # 2. Search knowledge base
        try:
            knowledge_results = qdrant_service.search(
                collection=settings.COLLECTION_KNOWLEDGE,
                query=query,
                top_k=3,
            )
            relevant_knowledge = [r for r in knowledge_results if r["score"] > 0.5]
            results["knowledge"] = len(relevant_knowledge)
            snippets.extend([r["text"] for r in relevant_knowledge])
        except Exception as e:
            logger.warning("Knowledge search failed: %s", e)
            results["knowledge"] = 0

        # 3. Search user preferences
        try:
            pref_results = qdrant_service.search(
                collection=settings.COLLECTION_USER_PREFS,
                query=query,
                top_k=2,
                filters={"user_id": user_id},
            )
            relevant_prefs = [r for r in pref_results if r["score"] > 0.5]
            results["preferences"] = len(relevant_prefs)
            snippets.extend([r["text"] for r in relevant_prefs])
        except Exception as e:
            logger.warning("Preference search failed: %s", e)
            results["preferences"] = 0

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "snippets": snippets,
                "sources": results,
                "total_results": len(snippets),
            },
        )


researcher_agent = ResearchAgent()
