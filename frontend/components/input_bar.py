import streamlit as st

def render_input_bar():
    """
    Render the input bar with file upload integrated.
    """
    col1, col2 = st.columns([9, 1])

    # 📎 File uploader
    with col2:
        uploaded_files = st.file_uploader(
            "📎", type=["pdf", "txt", "docx"], accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            st.success(f"{len(uploaded_files)} file(s) uploaded.")

    # 💬 Chat input
    with col1:
        user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.chat_history.append({
            "user": user_input,
            "agent": "Thinking..."  # Placeholder, replace with backend call
        })
        st.rerun()
