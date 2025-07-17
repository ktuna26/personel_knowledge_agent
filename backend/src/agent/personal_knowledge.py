# src/agent/personal_knowledge.py
"""
Core orchestrator for the Personal Knowledge Agent.
Handles prompt preparation, model interaction, and optional streaming.
"""

from time import time
from uuid import uuid4
from httpx import AsyncClient, HTTPStatusError
from typing import List, Dict, Union, AsyncGenerator

from openai import AsyncOpenAI # OpenAI impor
from langchain.schema import (
    HumanMessage, 
    AIMessage, 
    SystemMessage, 
    BaseMessage
) # Langchain import 

# Local imports
from src.rag.loader import load_and_chunk_documents
from src.rag.embedder import DocumentEmbedder
from src.rag.retriever import Retriever

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PersonalKnowledgeAgent:
    """
    Async wrapper for OpenAI ChatCompletion with streaming support.
    """

    def __init__(
        self,
        model_name: str = "gpt-4",
        temperature: float = 0.1,
        max_tokens: int = 512,
        stream: bool = False,
        rag_source_dir: str = None, 
    ):
        """
        Initializes the LLM agent.

        Args:
            model_name: The name of the OpenAI model to use.
            temperature: Sampling temperature (randomness).
            max_tokens: Max tokens allowed in the response.
            stream: If True, enables token-by-token streaming.
        """
        self.stream = stream
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # RAG
        self.rag_enabled = rag_source_dir is not None
        self.rag_source_dir = rag_source_dir
        if self.rag_enabled:
            docs = load_and_chunk_documents(rag_source_dir)
            self.embedder = DocumentEmbedder()
            doc_embeddings = self.embedder.embed_documents(docs)
            self.retriever = Retriever(self.embedder.embedding_model, docs, doc_embeddings)
            logger.info(f"RAG enabled: loaded {len(docs)} docs from {rag_source_dir}")
        else:
            self.retriever = None
            logger.info("RAG disabled (no source dir provided)")

        logger.info(
            f"PersonalKnowledgeAgent initialized (model={model_name}, streaming={stream})"
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert message dicts to OpenAI API chat message dicts.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.

        Returns:
            List of OpenAI chat message dicts.
        """
        converted = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in ("user", "assistant", "system"):
                converted.append({"role": role, "content": content})
            else:
                logger.warning(f"Unsupported message role '{role}' — skipping.")
        return converted
    
    def retrieve_context(self, user_query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve top-K relevant docs as chat messages (system role).
        """
        if not self.rag_enabled or not self.retriever:
            return []
        retrieved_docs = self.retriever.query(user_query, top_k=top_k)
        context_messages = []
        for doc in retrieved_docs:
            # You can be fancy here, but simple "system" message is fine
            context_messages.append({
                "role": "system",
                "content": f"[CONTEXT] {doc.page_content[:1500]}",
            })
        return context_messages
    
    async def run(
        self,
        messages: List[Dict[str, str]],
        include_context: bool = True,
        context_messages: List[Dict[str, str]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generates a response from the LLM.

        Args:
            messages: Chat history messages.
            include_context: Whether to prepend context.
            context_messages: List of context messages.
            
        Returns:
            If streaming: Async generator yielding chunks of content.
            Else: Full response string.
        """
        try:
            chat_messages = self._convert_messages(messages)

            if include_context :
                user_message = next((m for m in reversed(chat_messages) if m["role"] == "user"), None)
                if user_message and self.rag_enabled:
                    context_msgs = self.retrieve_context(user_message["content"], top_k=3)
                    chat_messages = context_msgs + chat_messages
            elif context_messages:
                # for explicit context use
                chat_messages = context_messages + chat_messages

            if self.stream:
                # Async streaming generator
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=chat_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True,
                )
                
                async def generator():
                    index = 0
                    async for chunk in response:
                        delta = chunk.choices[0].delta
                        content = getattr(delta, "content", None)
                        if content:
                            yield {
                                "id": f"chatcmpl-{uuid4().hex}",
                                "object": "chat.completion.chunk",
                                "created": int(time()),
                                "model": self.model_name,
                                "choices": [{
                                    "delta": {"content": content},
                                    "index": index,
                                    "finish_reason": None
                                }]
                            }
                            index += 1
                    # Final stop chunk
                    yield {
                        "id": f"chatcmpl-{uuid4().hex}",
                        "object": "chat.completion.chunk",
                        "created": int(time()),
                        "model": self.model_name,
                        "choices": [{
                            "delta": {},
                            "index": index,
                            "finish_reason": "stop"
                        }]
                    }
                return generator()
            
            # Non-streaming full response
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=chat_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("LLM inference failed", exc_info=True)
            return "❌ LLM response generation failed."

    async def list_models(self) -> dict:
        """
        Asynchronously fetches available models from OpenAI.

        Returns:
            JSON response from the OpenAI /models endpoint.

        Raises:
            HTTPStatusError: If the OpenAI API call fails.
            Exception: For any other unexpected error.
        """
        try:
            async with AsyncClient() as client:
                response = await client.get(
                    url="https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()
        except HTTPStatusError as exc:
            logger.error(f"HTTP error while fetching models: {exc}")
            raise
        except Exception as exc:
            logger.error("Unexpected error while fetching models", exc_info=True)
            raise
