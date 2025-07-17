# src/components/footer.py
"""
Footer UI component for the Personal Knowledge Agent Streamlit app.
Renders a fixed footer with adaptive styling and copyright info.
"""

import streamlit as st # Streamlit import
from src.utils.logger import get_logger # Local import

# Logger
logger = get_logger(__name__)


def render_footer() -> None:
    """
    Renders the persistent footer at the bottom of the page.
    """
    with st.sidebar:
        # Add enough empty lines to push footer to bottom
        for _ in range(10):
            st.markdown(" ")
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.85rem; color: #888;">
                © 2025 Personal Knowledge Agent. All rights reserved.
            </div>
            """,
            unsafe_allow_html=True
        )
        logger.debug("Footer rendered.")
