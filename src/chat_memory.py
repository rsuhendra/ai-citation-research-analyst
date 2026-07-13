import streamlit as st


def ensure_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


def add_message(role: str, content: str, **metadata) -> None:
    st.session_state["messages"].append(
        {"role": role, "content": content, **metadata}
    )


def conversation_context(max_messages: int = 8) -> str:
    messages = st.session_state.get("messages", [])[-max_messages:]
    lines = [
        f"{message.get('role', 'user').capitalize()}: {message.get('content', '')}"
        for message in messages
    ]
    return "\n".join(lines) or "No prior conversation."
