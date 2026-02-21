"""
Jarvis Control Tower — Executor Agent
Executes the action plan by calling tools and services.
"""
import logging
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput
from services.ollama_client import ollama_client
from services.memory import memory_service
from services.n8n_client import n8n_client

logger = logging.getLogger(__name__)


class ExecutorAgent(BaseAgent):
    """Executes action plans by dispatching to appropriate services."""

    name = "executor"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        plan = agent_input.metadata.get("plan", {})
        steps = plan.get("steps", [])
        results = []
        final_response = ""

        for i, step in enumerate(steps):
            action = step.get("action", "")
            params = step.get("params", {})
            logger.info("[executor] Step %d: %s", i + 1, action)

            try:
                step_result = await self._dispatch(action, params, agent_input)
                results.append({
                    "step": i + 1,
                    "action": action,
                    "success": True,
                    "result": step_result,
                })

                # Capture the last LLM response as the final reply
                if action == "llm_generate":
                    final_response = step_result.get("response", "")

            except Exception as e:
                logger.error("[executor] Step %d failed: %s", i + 1, str(e))
                results.append({
                    "step": i + 1,
                    "action": action,
                    "success": False,
                    "error": str(e),
                })

        # If no LLM generation step produced a response, generate one
        if not final_response:
            final_response = await self._generate_fallback_response(agent_input)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "response": final_response,
                "step_results": results,
            },
        )

    async def _dispatch(self, action: str, params: dict, agent_input: AgentInput) -> dict:
        """Route an action to the appropriate service."""

        if action == "memory_search":
            query = params.get("query", agent_input.text)
            results = memory_service.search_knowledge(query)
            return {"matches": results}

        elif action == "memory_store":
            text = params.get("text", agent_input.text)
            point_id = memory_service.store_knowledge(
                text=text,
                metadata={"user_id": agent_input.user_id, "intent": str(agent_input.intent)},
            )
            return {"stored": True, "point_id": point_id}

        elif action == "n8n_trigger":
            workflow = params.get("workflow", "default")
            payload = {
                "user_id": agent_input.user_id,
                "text": agent_input.text,
                "intent": str(agent_input.intent),
                **params,
            }
            result = await n8n_client.trigger_webhook(workflow, payload)
            return result

        elif action == "llm_generate":
            task = params.get("task", "respond")
            response = await self._llm_generate(task, agent_input)
            return {"response": response}

        elif action == "n8n_health_check":
            healthy = await n8n_client.is_healthy()
            ollama_ok = await ollama_client.is_healthy()
            return {
                "n8n": "healthy" if healthy else "unhealthy",
                "ollama": "healthy" if ollama_ok else "unhealthy",
            }

        else:
            logger.warning("[executor] Unknown action: %s", action)
            return {"skipped": True, "reason": f"Unknown action: {action}"}

    async def _llm_generate(self, task: str, agent_input: AgentInput) -> str:
        """Generate a response using the LLM based on task type."""
        context_str = ""
        if agent_input.context:
            context_str = "\n\nRelevant context:\n" + "\n".join(f"- {c}" for c in agent_input.context)

        if task == "confirm":
            prompt = f"Generate a brief, friendly confirmation that the following request has been processed:\n{agent_input.text}"
        elif task == "answer":
            prompt = f"Answer the following question using the provided context.{context_str}\n\nQuestion: {agent_input.text}"
        elif task == "report":
            step_results = agent_input.metadata.get("step_results", [])
            prompt = f"Generate a brief system health report based on these check results:\n{step_results}"
        else:
            prompt = f"Respond helpfully to this message:{context_str}\n\n{agent_input.text}"

        system = "You are Jarvis, a helpful personal AI assistant. Be concise and friendly."
        return await ollama_client.generate(prompt, system=system)

    async def _generate_fallback_response(self, agent_input: AgentInput) -> str:
        """Generate a response when no plan step produced one."""
        return await self._llm_generate("respond", agent_input)


executor_agent = ExecutorAgent()
