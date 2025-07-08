import streamlit as st
from components.chat_ui import render_chat_history
from components.input_bar import render_input_bar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Personal Knowledge Agent", layout="wide")

# ------------------------
# 🔁 Initialize session state
# ------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ------------------------
# 🧠 Sidebar
# ------------------------
render_sidebar()

# ------------------------
# 🧱 Main Layout
# ------------------------
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)
st.title("🧠 Personal Knowledge Agent")

# Main chat history
render_chat_history()

# Chat input & file upload
render_input_bar()
