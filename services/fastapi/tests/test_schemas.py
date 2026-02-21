"""Tests for Pydantic schemas and model validation."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.schemas import (
    Intent,
    AgentInput,
    AgentOutput,
    OrchestrateRequest,
    OrchestrateResponse,
    MemoryStoreRequest,
    MemorySearchRequest,
    HealthResponse,
)


class TestIntentEnum:
    def test_intent_values(self):
        assert Intent.REMINDER == "reminder"
        assert Intent.NOTE == "note"
        assert Intent.QUESTION == "question"
        assert Intent.UNKNOWN == "unknown"

    def test_intent_from_string(self):
        assert Intent("reminder") == Intent.REMINDER
        assert Intent("unknown") == Intent.UNKNOWN

    def test_invalid_intent_raises(self):
        with pytest.raises(ValueError):
            Intent("not_an_intent")


class TestAgentInput:
    def test_minimal_input(self):
        inp = AgentInput(user_id="user1", text="hello")
        assert inp.user_id == "user1"
        assert inp.text == "hello"
        assert inp.intent is None
        assert inp.context == []
        assert inp.metadata == {}

    def test_full_input(self):
        inp = AgentInput(
            user_id="user1",
            text="hello",
            intent=Intent.QUESTION,
            context=["past context"],
            metadata={"key": "value"},
        )
        assert inp.intent == Intent.QUESTION
        assert len(inp.context) == 1


class TestAgentOutput:
    def test_success_output(self):
        out = AgentOutput(
            agent_name="test",
            success=True,
            data={"reply": "hi"},
        )
        assert out.agent_name == "test"
        assert out.success is True
        assert out.error is None

    def test_failure_output(self):
        out = AgentOutput(
            agent_name="test",
            success=False,
            error="something broke",
        )
        assert out.success is False
        assert out.error == "something broke"


class TestOrchestrateSchemas:
    def test_request(self):
        req = OrchestrateRequest(user_id="u1", text="what time is it?")
        assert req.user_id == "u1"

    def test_response_defaults(self):
        resp = OrchestrateResponse(reply="hello", intent="question")
        assert resp.trace == []
        assert resp.run_id == ""


class TestMemorySchemas:
    def test_store_request_defaults(self):
        req = MemoryStoreRequest(user_id="u1", text="remember this")
        assert req.memory_type == "knowledge"
        assert req.metadata == {}

    def test_search_request_defaults(self):
        req = MemorySearchRequest(user_id="u1", query="something")
        assert req.memory_type == "conversations"
        assert req.top_k == 5


class TestHealthResponse:
    def test_defaults(self):
        resp = HealthResponse(status="ok")
        assert resp.services == {}
        assert resp.timestamp == ""
