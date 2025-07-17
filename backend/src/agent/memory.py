"""
Agent memory management module.
Stores and retrieves chat context, conversation state, summaries, etc.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AgentMemory:
    def __init__(self):
        self.chat_history: List[Dict[str, Any]] = []

    def update(self, messages: List[Dict[str, Any]]) -> None:
        """
        Update chat memory with the latest messages.

        Args:
            messages (List[Dict]): List of chat messages.
        """
        logger.debug("Updating memory with latest messages.")
        self.chat_history = messages.copy()

    def update_agent_response(self, response: str) -> None:
        """
        Add agent response to the memory.

        Args:
            response (str): Agent's reply text.
        """
        logger.debug("Adding agent response to memory.")
        self.chat_history.append({"role": "assistant", "content": response})

    def retrieve(self) -> List[Dict[str, Any]]:
        """
        Retrieve current memory contents.

        Returns:
            List[Dict]: Current chat history.
        """
        logger.debug("Retrieving memory contents.")
        return self.chat_history.copy()
