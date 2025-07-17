# main.py
"""
Main entry point for the Streamlit chat application.

This module sets up the UI layout, manages session state for chat history,
handles user input, and interacts with the Agent backend service to process
chat queries with optional streaming responses.

Usage:
    streamlit run app.py

Testing:
    Access http://localhost:8501 in your browser and send chat messages.
"""

import streamlit as st

# Local imports
from src.services.agent import AgentService
from src.components.footer import render_footer
from src.components.sidebar import render_sidebar
from src.components.chat_ui import (
    init_messages,
    render_chat_history,
    process_user_input,
)
from src.config.settings import settings
from src.utils.logger import configure_logging, get_logger

# Configure logging based on settings
configure_logging(settings)
logger = get_logger(__name__)


logger.info("Starting Streamlit chat application.")

# -------------------------- #
# Set page configs and title #
# -------------------------- #
st.set_page_config(
    page_title=settings.agent_name,
    layout=settings.st_layout,
    page_icon=settings.page_icon,
)
st.title(f"{settings.agent_name} 🕵\n---")

# -------------------------------- #
# Render sidebar before everything #
# -------------------------------- #
render_sidebar()

# ------------------------ #
# Initialize session state #
# ------------------------ #
init_messages()

# --------------------------------------- #
# Ensure AgentService is in session state #
# --------------------------------------- #
if "agent_service" not in st.session_state:
    st.session_state["agent_service"] = AgentService("http://localhost:8010/v1/chat/completions")

# -------------- #
# Get user input #
# -------------- #
user_input = st.chat_input("Type your query here...")

# ------------------------------------- #
# Render chat history before user input #
# ------------------------------------- #
render_chat_history()

# --------------------------------------------------- #
# Process input and update state (NO RENDERING here!) #
# --------------------------------------------------- #
if user_input:
    try:
        process_user_input(
            user_input,
            st.session_state["agent_service"],
            stream=st.session_state.get("enable_streaming", True)
    )
    except Exception as exc:
        logger.error("Unhandled error during processing user input.", exc_info=True)
        st.error("❌ An unexpected error occurred. Please try again.")

# Optional footer
render_footer()
