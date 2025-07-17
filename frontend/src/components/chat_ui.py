# src/components/chat_ui.py
"""
Handles chat history rendering and user-agent interaction logic.
Provides robust and efficient chat UI for the Streamlit frontend.
"""

import streamlit as st
from typing import Optional, Generator
from json import loads, JSONDecodeError

# Local imports
from src.services.agent import AgentService
from src.config.settings import settings
from src.utils.logger import get_logger

# Logger
logger = get_logger(__name__)


def _append_message(role: str, content: str) -> None:
    """
    Appends a message to the Streamlit session state.
    Args:
        role: The sender's role ("user" or "assistant").
        content: The text content of the message.
    """
    if settings.session_key not in st.session_state:
        st.session_state[settings.session_key] = []
        logger.warning("Session key missing; re-initializing message history.")

    st.session_state[settings.session_key].append({"role": role, "content": content})
    logger.debug(f"Appended {role} message: {content[:80]}...")

def _get_agent_response(
    agent_service: AgentService, stream: bool = False
) -> Generator[str, None, None]:
    """
    Gets a response from the agent, streaming or non-streaming.
    Args:
        agent_service: The agent client instance.
        stream: Whether to use streaming.
    Yields:
        Each text chunk (if streaming) or the full reply (if non-streaming).
    """
    try:
        chat_history = st.session_state.get(settings.session_key, [])
        if stream:
            for chunk_json_str in agent_service.send_chat_history(chat_history, 
                                                                  stream=True,
                                                                  include_context = st.session_state.enable_memory
                                                                ):
                try:
                    chunk = loads(chunk_json_str)
                    choices = chunk.get("choices", [])
                    if choices:
                        content_part = choices[0].get("delta", {}).get("content", "")
                        if content_part:
                            yield content_part  # Yield each incremental text part
                except JSONDecodeError:
                    logger.warning(f"Malformed JSON from agent: {chunk_json_str}")
            logger.info("Agent responded (streaming).")
        else:
            with st.spinner("Agent is thinking..."):
                response = agent_service.send_chat_history(chat_history,
                                                           include_context = st.session_state.enable_memory
                                                        )
            content = response.get("content", "⚠️ No response received.")
            reasoning = response.get("reasoning", [])
            if reasoning:
                content += "\n\n---\n**Reasoning:**\n" + "\n".join(reasoning)
            logger.info("Agent responded (non-stream).")
            yield content  # Yield once for non-streaming
    except Exception as exc:
        logger.error("AgentService error", exc_info=True)
        yield f"❌ Error communicating with agent. {str(exc)}"

def init_messages() -> None:
    """
    Ensures chat history is initialized in Streamlit session state.
    """
    if settings.session_key not in st.session_state:
        st.session_state[settings.session_key] = []
        logger.debug("Initialized empty chat message history.")

def render_chat_history() -> None:
    """
    Renders all chat history messages in the Streamlit UI.
    """
    history = st.session_state.get(settings.session_key, [])
    if not history:
        st.info("No chat yet—start by sending a message!")
        return
    for msg in history:
        avatar = settings.avatar_user if msg["role"] == "user" else settings.avatar_assistant
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

def process_user_input(
    user_input: str,
    agent_service: AgentService,
    stream: Optional[bool] = False
) -> None:
    """
    Processes user input, invokes the agent backend, and updates the UI.
    Args:
        user_input: The text entered by the user.
        agent_service: The backend agent service.
        stream: Whether to use streaming response.
    """
    user_input = user_input.strip()
    if not user_input:
        st.warning("Please enter a message before sending.")
        return

    _append_message("user", user_input)
    with st.chat_message("user", avatar=settings.avatar_user):
        st.markdown(user_input)

    if stream:
        with st.chat_message("assistant", avatar=settings.avatar_assistant):
            placeholder = st.empty()
            response_generator = _get_agent_response(agent_service, stream=True)
            assistant_message = ""
            # Spinner for first chunk only
            with st.spinner("Agent is thinking..."):
                try:
                    first_chunk = next(response_generator)
                    assistant_message += first_chunk
                    placeholder.markdown(assistant_message)
                except StopIteration:
                    st.warning("No response received.")
                    return
            # Continue streaming without spinner
            for chunk in response_generator:
                assistant_message += chunk
                placeholder.markdown(assistant_message)
            _append_message("assistant", assistant_message)
    else:
        # Spinner is inside _get_agent_response for non-streaming
        response = next(_get_agent_response(agent_service, stream=False))
        _append_message("assistant", response)
        with st.chat_message("assistant", avatar=settings.avatar_assistant):
            st.markdown(response)

    # Single rerun to update UI and controls
    st.rerun()
