"""
Entry point for the Personal Knowledge Agent API.

To Run:
-------
    uvicorn main:app --host 0.0.0.0 --port 8010

To Test:
--------
- Swagger UI: http://localhost:8010/docs
- Postman: See `tests/postman_collection.json`
"""

from time import time
from json import dumps
from uuid import uuid4
from typing import List
from asyncio import sleep
from pydantic import BaseModel, Field # Pydantic import

# FastAPI imports
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Loca imports
from src.config.settings import settings
from src.utils.logger import configure_logging, get_logger
from src.agent.personal_knowledge import PersonalKnowledgeAgent

# Initialize logging
configure_logging(settings)
logger = get_logger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Personal Knowledge Agent API",
    description="An AI-powered backend for interacting with your knowledge base.",
    version="1.0.0",
    openapi_url="/openapi.json",  # Explicitly set the OpenAPI URL
    docs_url="/docs"              # Set the docs URL with the desired prefix
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your allowed origins, e.g. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- #
# Pydantic Schemas #
# ---------------- #
class Message(BaseModel):
    """OpenAI-compatible message schema"""
    role: str  # "system" | "user" | "assistant"
    content: str

class RequestBody(BaseModel):
    """OpenAI /v1/chat/completions request format
    
    Required Fields:
    - model: Specifies the model version.
    - messages: List of chat messages exchanged.

    Optional Fields:
    - max_tokens: Maximum number of tokens in response (default: 512).
    - temperature: Controls randomness of responses (default: 0.7, range: 0.0 - 1.0).
    - streaming: Enables or disables response streaming (default: False).
    - include_context: Specifies whether to include context in responses (default: False).
    """
    model: str
    messages: list[Message]
    max_tokens: int = Field(default=512, ge=1, description="Maximum tokens in the response")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Controls randomness of responses")
    stream: bool = Field(default=False, description="Enables response streaming")
    include_context: bool = Field(default=False, description="Includes context in responses")

# ----------------- #
# Model Call Back  #
# ----------------- #
async def get_agent(
    request: RequestBody
) -> PersonalKnowledgeAgent:
    """
    Dependency injection function for PersonalKnowledgeAgent instance.
    Initializes the agent with dynamic model_name, temperature, max_tokens, and streaming.
    """
    return PersonalKnowledgeAgent(
        model_name=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
        rag_source_dir="data/" 
    )

async def stream_chat_response(agent: PersonalKnowledgeAgent, messages: List[dict], include_context: bool):
    """
    Async generator for SSE-compliant OpenAI-compatible streaming output.
    """
    chunks = await agent.run(messages, include_context=include_context)
    async for chunk in chunks:
        yield f"data: {dumps(chunk)}\n\n"
        await sleep(0.001)
    yield "data: [DONE]\n\n"

# -------------- #
# API Endpoints  #
# -------------- #
@app.get("/health", summary="Health Check", tags=["System"])
async def health_check():
    """
    Simple health check endpoint to verify the API status.
    Returns:
    - JSONResponse with a status message
    """
    return JSONResponse(content={"status": "ok"})

@app.post("/v1/chat/completions", summary="OpenAI-compatible Chat Completion", tags=["Chat"])
async def chat_completions(
    request: RequestBody,
    agent: PersonalKnowledgeAgent = Depends(get_agent),
):
    """
    Handles chat completion requests and streams responses from PersonelKnowledgeAgent.
    
    Request Parameters:
    - **model**: Specifies the model version.
    - **messages**: List of chat messages exchanged.
    - **max_tokens** (Optional): Maximum number of tokens in response.
    - **temperature** (Optional): Controls randomness of responses.
    - **streaming** (Optional): Enables or disables response streaming.
    - **include_context** (Optional): Specifies whether to include context in responses.

    Returns:
    - StreamingResponse if stream=True, otherwise a JSON response.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")

    request_id = uuid4().hex[:6]
    logger.info(f"[{request_id}] User: {request.messages[-1].content}")

    try:
        messages_dicts = [m.dict() for m in request.messages]
        
        if request.stream:
            return StreamingResponse(
                stream_chat_response(agent, messages_dicts, request.include_context),
                media_type="text/event-stream",
            )
        
        # Non-streaming response
        output = await agent.run(
            [m.dict() for m in request.messages],
            include_context=request.include_context
        )
        response = {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion",
            "created": int(time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": output
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": None  # Optional: implement token usage tracking if needed
        }
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"[{request_id}] Completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat completion failed.")

# Available models
@app.get("/v1/models", summary="List available models", tags=["OpenAI-Compatible"])
async def list_models():
    try:
        agent = PersonalKnowledgeAgent()
        models = await agent.list_models()
        return JSONResponse(content=models)
    except Exception as e:
        logger.error(f"Model listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch models")

logger.info("Personal Knowledge Agent API started successfully.")
