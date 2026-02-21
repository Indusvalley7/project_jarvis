"""
Jarvis Control Tower — Ollama Client
Wrapper for the Ollama REST API.
"""
import httpx
import json
import logging
from config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama LLM inference."""

    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT

    async def generate(self, prompt: str, system: str = None) -> str:
        """
        Send a prompt to Ollama and return the raw text response.

        Args:
            prompt: The user/task prompt
            system: Optional system prompt for behavior control

        Returns:
            Raw text response from the model
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %ds", self.timeout)
            raise
        except Exception as e:
            logger.error("Ollama request failed: %s", str(e))
            raise

    async def generate_json(self, prompt: str, system: str = None) -> dict:
        """
        Send a prompt and parse the response as JSON.
        Falls back to a wrapper dict if JSON parsing fails.
        """
        raw = await self.generate(prompt, system)

        # Try to extract JSON from the response (model may add extra text)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object within the text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse Ollama response as JSON: %s", raw[:200])
        return {"raw_response": raw}

    async def is_healthy(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


# Singleton instance
ollama_client = OllamaClient()
