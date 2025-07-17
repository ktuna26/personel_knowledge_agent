# src/components/sidebar.py
"""
Sidebar component for the Personal Knowledge Agent Streamlit app.
Includes config toggles, branding, and a chat history reset confirmation dialog.
"""

import streamlit as st # Streamlit import

# Local imports
from src.components.footer import render_footer
from src.config.settings import settings
from src.utils.logger import get_logger

# Initialize module-level logger
logger = get_logger(__name__)


@st.dialog("⚠️ Confirm Deletion")
def confirm_clear_dialog() -> None:
    """
    Confirmation dialog for clearing all chat history.
    """
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <h4>Are you sure you want to clear all chat history?</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        btn_confirm, btn_cancel = st.columns(2)

        with btn_confirm:
            if st.button("✅ Yes, clear", use_container_width=True):
                if settings.session_key in st.session_state:
                    st.session_state.pop(settings.session_key, None)
                    logger.info("Chat history cleared via confirmation dialog.")
                else:
                    logger.warning("Attempted to clear chat history, but session key was not found.")
                st.rerun()

        with btn_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                logger.info("Chat history clear canceled by user.")
                st.rerun()


def render_sidebar():
    """
    Render the sidebar with logo, feature toggles, and clear chat control.
    """
    with st.sidebar:
        st.image("assets/logo.png", width=120)
        st.markdown("# ⚙️ Settings")

        # Configurable features
        enable_memory = st.toggle("🧠 Enable Memory", key="enable_memory", value=True)
        enable_streaming = st.toggle("💬 Stream Responses", key="enable_streaming", value=True)
        logger.debug(f"Sidebar toggles - Memory: {enable_memory}, Streaming: {enable_streaming}")

        st.markdown("")

        # Clear chat button
        if st.button(
            "🧹 **Clear Chat History**",
            key="clear_chat_btn",
            disabled=not bool(st.session_state.get(settings.session_key))
        ):
            logger.info("Clear chat button clicked.")
            confirm_clear_dialog()

        st.markdown("---")

        # Help link
        st.markdown("[🔑 Get your OpenAI API key](https://platform.openai.com/account/api-keys)")
