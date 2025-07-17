# src/services/agent.py
"""
Service module for communicating with an AI-powered agent API.
Handles sending chat history and formatting the agent response.

Usage:
    from services.agent import AgentService

    api_url = getenv("AGENT_API_URL", "http://localhost:8010/openai/deployments/DataLoaderAgent/chat/completions")
    api_key = getenv("AGENT_API_KEY", "test")

    agent = AgentService(
        api_url=api_url
        api_key=api_key,
        timeout=120
    )

    chat_history = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi! How can I help you?"}
    ]

    result = agent.send_chat_history(chat_history)
    print(result["content"])
"""
from typing import Any, Dict, List, Generator, Union
from requests import RequestException, post
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentServiceException(Exception):
    """Exception raised for errors in the AgentService communication."""


class AgentService:
    """
    Client for communicating with an external AI Agent service.

    Supports sending chat history with optional streaming responses.
    """

    def __init__(self, api_url: str, timeout: int = 60) -> None:
        """
        Initialize the AgentService client.

        Args:
            api_url: The URL of the agent service API.
            timeout: Request timeout in seconds. Defaults to 60.

        Raises:
            ValueError: If `api_url` is empty.
        """
        if not api_url:
            raise ValueError("AgentService requires a non-empty api_url.")
        self.api_url = api_url
        self.timeout = timeout

    def send_chat_history(
        self,
        chat_history: List[Dict[str, Any]],
        model: str = "gpt-4",
        temperature: float = 0.1,
        max_tokens: int = 512,
        include_context: bool = False,
        stream: bool = False,
        n_last: int = 30,
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """
        Send recent chat messages to the agent and receive a response.

        Args:
            chat_history: Full chat history as list of message dicts.
            model: LLM model name. Defaults to "gpt-4".
            temperature: Sampling temperature. Defaults to 0.1.
            max_tokens: Max tokens in response. Defaults to 512.
            include_context: Include additional context if supported. Defaults to False.
            stream: Whether to receive streaming response. Defaults to False.
            n_last: Number of recent messages to include from chat history. Defaults to 30.

        Returns:
            - Non-streaming: Dict with 'content' and optional 'reasoning'.
            - Streaming: Generator yielding JSON string chunks.

        Notes:
            Streaming response yields lines without the 'data: ' prefix.
        """
        # Filter and prepare the last n_last valid messages
        recent_messages = [
            {"role": msg.get("role", ""), "content": msg.get("content", "")}
            for msg in chat_history[-n_last:]
            if msg.get("role") and msg.get("content")
        ]

        payload = {
            "model": model,
            "messages": recent_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "include_context": include_context,
        }

        try:
            if stream:
                response = post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout,
                    stream=True,
                )
                response.raise_for_status()

                def stream_generator() -> Generator[str, None, None]:
                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data = line[len("data: "):].strip()
                            if data == "[DONE]":
                                break
                            if data:  # Defensive: ensure non-empty chunk
                                yield data

                return stream_generator()

            # Non-streaming response
            response = post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_response(response.json())

        except RequestException as exc:
            logger.error(f"[AgentService] Request error: {exc}", exc_info=True)
            return {"content": f"❌ Request error: {str(exc)}", "reasoning": []}
        except Exception as exc:
            logger.error(f"[AgentService] Unexpected error: {exc}", exc_info=True)
            return {"content": f"❌ Unexpected error: {str(exc)}", "reasoning": []}

    @staticmethod
    def _parse_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the agent's non-streaming JSON response.

        Args:
            data (Dict[str, Any]): The JSON-decoded response from the agent.

        Returns:
            Dict[str, Any]: Parsed dict with 'content' and optional 'reasoning'.
        """
        if "response" in data:
            return {"content": data["response"], "reasoning": []}

        # Support OpenAI-like response format
        if "choices" in data and isinstance(data["choices"], list):
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content")
            if content:
                return {"content": content, "reasoning": []}

        logger.warning("No valid response content found in agent reply.")
        return {"content": "⚠️ No response field found.", "reasoning": []}
