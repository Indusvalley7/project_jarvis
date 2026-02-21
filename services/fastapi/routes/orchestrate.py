"""
Jarvis Control Tower — Orchestration Route
Main endpoint that runs the full agent pipeline.
Persists runs and steps to Postgres.
Pipeline: Classifier → Planner → Researcher → Executor → Tool Router → Critic
"""
import time
import logging
from fastapi import APIRouter
from models.schemas import (
    OrchestrateRequest,
    OrchestrateResponse,
    AgentInput,
)
from agents.classifier import classifier_agent
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.executor import executor_agent
from agents.tool_router import tool_router_agent
from agents.critic import critic_agent
from services.memory import memory_service
from services.database import db

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_RETRIES = 1  # Max times the critic can request re-execution


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(payload: OrchestrateRequest):
    """
    Main orchestration endpoint.
    Pipeline: Classify → Plan → Research → Execute → Tool Route → Critique
    Persists everything to Postgres.
    """
    start = time.time()

    # Ensure user exists in Postgres
    await db.ensure_user(payload.user_id)

    # Create run in Postgres
    run_id = await db.create_run(payload.user_id, payload.text)

    try:
        # --- Step 1: Classify Intent ---
        agent_input = AgentInput(user_id=payload.user_id, text=payload.text)
        classify_result = await classifier_agent.run(agent_input)

        await db.create_run_step(
            run_id=run_id,
            step_name="classifier",
            input_json={"text": payload.text},
            output_json=classify_result.data if classify_result.success else None,
            error=classify_result.error if not classify_result.success else None,
            latency_ms=classify_result.duration_ms,
        )

        intent = classify_result.data.get("intent", "unknown")
        clean_text = classify_result.data.get("clean_text", payload.text)

        # --- Step 2: Plan ---
        plan_input = AgentInput(
            user_id=payload.user_id,
            text=clean_text,
            intent=intent,
        )
        plan_result = await planner_agent.run(plan_input)

        await db.create_run_step(
            run_id=run_id,
            step_name="planner",
            input_json={"text": clean_text, "intent": intent},
            output_json=plan_result.data if plan_result.success else None,
            error=plan_result.error if not plan_result.success else None,
            latency_ms=plan_result.duration_ms,
        )

        # --- Step 3: Research (Qdrant search) ---
        research_input = AgentInput(
            user_id=payload.user_id,
            text=clean_text,
            intent=intent,
        )
        research_result = await researcher_agent.run(research_input)

        await db.create_run_step(
            run_id=run_id,
            step_name="researcher",
            input_json={"query": clean_text},
            output_json=research_result.data if research_result.success else None,
            error=research_result.error if not research_result.success else None,
            latency_ms=research_result.duration_ms,
        )

        # Inject research context
        context = research_result.data.get("snippets", [])

        # --- Step 4: Execute (with retry loop) ---
        response_text = ""
        for attempt in range(MAX_RETRIES + 1):
            exec_input = AgentInput(
                user_id=payload.user_id,
                text=clean_text,
                intent=intent,
                context=context,
                metadata={"plan": plan_result.data},
            )
            exec_result = await executor_agent.run(exec_input)

            await db.create_run_step(
                run_id=run_id,
                step_name="executor",
                input_json={"text": clean_text, "plan": plan_result.data},
                output_json=exec_result.data if exec_result.success else None,
                error=exec_result.error if not exec_result.success else None,
                latency_ms=exec_result.duration_ms,
            )

            response_text = exec_result.data.get("response", "I couldn't process that request.")

            # --- Step 5: Tool Router ---
            tool_input = AgentInput(
                user_id=payload.user_id,
                text=payload.text,
                intent=intent,
                metadata={"chat_id": payload.user_id, "response": response_text},
            )
            tool_result = await tool_router_agent.run(tool_input)

            await db.create_run_step(
                run_id=run_id,
                step_name="tool_router",
                input_json={"intent": intent, "text": payload.text},
                output_json=tool_result.data if tool_result.success else None,
                error=tool_result.error if not tool_result.success else None,
                latency_ms=tool_result.duration_ms,
            )

            # --- Step 6: Critique ---
            critic_input = AgentInput(
                user_id=payload.user_id,
                text=payload.text,
                intent=intent,
                metadata={"executor_response": response_text},
            )
            critic_result = await critic_agent.run(critic_input)

            await db.create_run_step(
                run_id=run_id,
                step_name="critic",
                input_json={"response": response_text},
                output_json=critic_result.data if critic_result.success else None,
                error=critic_result.error if not critic_result.success else None,
                latency_ms=critic_result.duration_ms,
            )

            if critic_result.data.get("pass", True):
                break
            else:
                logger.info("[run:%s] Critic rejected (attempt %d): %s",
                            run_id, attempt + 1, critic_result.data.get("feedback"))

        # --- Save Interaction to Memory ---
        try:
            memory_service.save_interaction(
                user_id=payload.user_id,
                message=payload.text,
                intent=intent,
                response=response_text,
            )
        except Exception as e:
            logger.warning("Failed to save interaction to memory: %s", str(e))

        # --- Complete Run ---
        total_ms = (time.time() - start) * 1000
        await db.complete_run(run_id, intent, response_text, total_ms)

        # Build trace from Postgres
        run_data = await db.get_run(run_id)
        trace = run_data.get("steps", []) if run_data else []

        return OrchestrateResponse(
            reply=response_text,
            intent=intent,
            trace=trace,
            run_id=run_id,
        )

    except Exception as e:
        total_ms = (time.time() - start) * 1000
        await db.fail_run(run_id, str(e), total_ms)
        logger.error("[run:%s] Pipeline failed: %s", run_id, str(e))
        return OrchestrateResponse(
            reply=f"Sorry, I encountered an error: {str(e)}",
            intent="unknown",
            run_id=run_id,
        )
