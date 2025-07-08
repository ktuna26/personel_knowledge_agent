import streamlit as st

def render_chat_history():
    """
    Render the scrollable chat history container.
    """
    st.markdown(
        """
        <style>
        .chat-container {
            height: 60vh;
            overflow-y: auto;
            padding: 1rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        for chat in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(chat["user"])
            with st.chat_message("assistant"):
                st.markdown(chat["agent"])

        st.markdown('</div>', unsafe_allow_html=True)
