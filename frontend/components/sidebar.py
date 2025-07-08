import streamlit as st

def render_sidebar():
    """
    Render the sidebar with config toggles and logo.
    """
    with st.sidebar:
        st.image("assets/logo.png", width=120)
        st.markdown("## ⚙️ Settings")
        st.toggle("Enable Memory", key="enable_memory", value=True)
        st.toggle("Stream Responses", key="enable_streaming", value=True)
        st.markdown("---")
        st.markdown("Built with ❤️ using GPT-4 + LangGraph")
