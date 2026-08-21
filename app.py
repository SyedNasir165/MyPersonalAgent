"""
Streamlit UI for My Personal Agent.

This file is a thin presentation layer only. All agent logic,
tool routing, task planning, and execution live in agent.py
and its supporting modules (file_tools.py, python_tool.py,
memory.py). This file never re-implements any of that logic —
it only calls agent.handle_message() and renders the result.

It additionally manages multiple named chat conversations
(sidebar history, like a typical chat app), persisted to
chat_sessions.json so they survive an app restart.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

import agent


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="My Personal Agent",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# CHAT SESSION STORAGE
# =========================================================

SESSIONS_FILE = Path(__file__).parent / "chat_sessions.json"


def load_sessions():

    if not SESSIONS_FILE.exists():

        return {}

    try:

        with SESSIONS_FILE.open("r", encoding="utf-8") as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {}


def save_sessions(sessions):

    with SESSIONS_FILE.open("w", encoding="utf-8") as file:

        json.dump(
            sessions,
            file,
            indent=2,
            ensure_ascii=False
        )


def make_session_title(text):

    text = text.strip().replace("\n", " ")

    if len(text) > 40:

        text = text[:40].rstrip() + "..."

    return text or "New chat"


def response_to_text(response):

    if not response:

        return ""

    if response.get("mode") == "plan":

        return response.get("final_response") or ""

    result = response.get("result")

    if result is None:

        return ""

    return result if isinstance(result, str) else str(result)


def rebuild_conversation_memory(messages):

    """
    Restores agent.py's short-term conversation memory so a
    reopened chat can still answer follow-up questions with
    the right context.
    """

    agent.conversation_history.clear()

    for message in messages:

        if message["role"] == "user":

            agent.conversation_history.append(
                {
                    "role": "user",
                    "content": message["content"]
                }
            )

        elif message["role"] == "assistant":

            text = response_to_text(message.get("response"))

            if text:

                agent.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": text
                    }
                )


def create_new_session(sessions):

    session_id = uuid.uuid4().hex[:12]

    now = datetime.now().isoformat()

    sessions[session_id] = {
        "title": "New chat",
        "created": now,
        "updated": now,
        "messages": []
    }

    save_sessions(sessions)

    return session_id


def switch_to_session(session_id, sessions):

    st.session_state.session_id = session_id

    st.session_state.messages = sessions[session_id]["messages"]

    rebuild_conversation_memory(
        st.session_state.messages
    )


def delete_session(session_id, sessions):

    """
    Deletes a conversation. If the deleted conversation was
    the active one, switches to the most recently updated
    remaining conversation, or starts a fresh one if none
    are left.
    """

    was_active = session_id == st.session_state.get("session_id")

    sessions.pop(session_id, None)

    save_sessions(sessions)

    if was_active:

        if sessions:

            latest_session_id = max(
                sessions,
                key=lambda sid: sessions[sid].get("updated", "")
            )

            switch_to_session(
                latest_session_id,
                sessions
            )

        else:

            new_session_id = create_new_session(sessions)

            sessions.update(
                load_sessions()
            )

            switch_to_session(
                new_session_id,
                sessions
            )


def persist_current_session(sessions):

    session_id = st.session_state.session_id

    session = sessions.setdefault(
        session_id,
        {
            "title": "New chat",
            "created": datetime.now().isoformat(),
            "messages": []
        }
    )

    session["messages"] = st.session_state.messages

    session["updated"] = datetime.now().isoformat()

    if session.get("title", "New chat") == "New chat":

        first_user_message = next(
            (
                message["content"]
                for message in st.session_state.messages
                if message["role"] == "user"
            ),
            None
        )

        if first_user_message:

            session["title"] = make_session_title(
                first_user_message
            )

    save_sessions(sessions)


# =========================================================
# TOOL DISPLAY HELPERS
# =========================================================

TOOL_ICONS = {
    "CALCULATOR": "🧮",
    "DATETIME": "🕐",
    "WEB": "🌐",
    "MEMORY": "🧠",
    "PYTHON": "🐍",
    "FILE": "📄",
    "CHAT": "💬"
}


def render_single_result(outcome):

    tool = outcome.get("tool", "CHAT")
    icon = TOOL_ICONS.get(tool, "🤖")
    result = outcome.get("result")
    success = outcome.get("success", True)

    if not success:

        st.error(
            result or "The request could not be completed."
        )

    elif tool == "PYTHON":

        st.markdown(f"{icon} **Python result:**")
        st.code(result or "", language="text")

    else:

        st.markdown(
            f"{icon} {result if result not in (None, '') else '(no output)'}"
        )

    with st.expander("🔧 Tool used"):

        st.write(f"**{tool}**")


def render_plan_result(outcome):

    plan = outcome.get("plan", [])
    steps = outcome.get("steps", [])
    final_response = outcome.get("final_response")

    st.markdown(final_response or "Task plan completed.")

    with st.expander("📋 Task plan & step details"):

        for index, step_info in enumerate(steps, start=1):

            status_icon = "✅" if step_info.get("success", True) else "❌"
            tool = step_info.get("tool", "-")
            step_text = step_info.get("step", "")
            result = step_info.get("result")

            st.markdown(
                f"{status_icon} **Step {index}** "
                f"({tool}): {step_text}"
            )

            if result not in (None, ""):

                st.code(str(result), language="text")


def render_response(response):

    if response is None:

        st.error("The agent did not return a response.")

        return

    if response.get("mode") == "plan":

        render_plan_result(response)

    else:

        render_single_result(response)


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

sessions = load_sessions()

if "session_id" not in st.session_state:

    if sessions:

        latest_session_id = max(
            sessions,
            key=lambda sid: sessions[sid].get("updated", "")
        )

        switch_to_session(
            latest_session_id,
            sessions
        )

    else:

        new_session_id = create_new_session(sessions)

        sessions = load_sessions()

        switch_to_session(
            new_session_id,
            sessions
        )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    if st.button("➕ New chat", use_container_width=True):

        new_session_id = create_new_session(sessions)

        sessions = load_sessions()

        switch_to_session(
            new_session_id,
            sessions
        )

        st.rerun()

    st.markdown("**Conversations**")

    sorted_sessions = sorted(
        sessions.items(),
        key=lambda item: item[1].get("updated", ""),
        reverse=True
    )

    for session_id, session in sorted_sessions:

        is_active = session_id == st.session_state.session_id

        label = session.get("title") or "New chat"

        icon = "🟢" if is_active else "💬"

        row_col, delete_col = st.columns(
            [0.82, 0.18]
        )

        with row_col:

            if st.button(
                f"{icon} {label}",
                key=f"session_btn_{session_id}",
                use_container_width=True
            ):

                if not is_active:

                    switch_to_session(
                        session_id,
                        sessions
                    )

                    st.rerun()

        with delete_col:

            if st.button(
                "🗑️",
                key=f"session_delete_{session_id}",
                use_container_width=True,
                help="Delete this conversation"
            ):

                delete_session(
                    session_id,
                    sessions
                )

                st.rerun()

    st.markdown("---")

    st.header("About")

    st.markdown(
        "This agent can use tools to help you:\n"
        "- 🧮 Calculator\n"
        "- 🕐 Date & Time\n"
        "- 🌐 Web search\n"
        "- 🧠 Memory (remember / recall)\n"
        "- 🐍 Python execution\n"
        "- 📄 File operations\n"
        "- 📋 Multi-step task planning & execution"
    )

    st.markdown("---")

    st.caption(
        "**Model:** this agent currently runs on a local "
        "Ollama installation using **phi3:mini**. It requires "
        "Ollama to be running on the same machine as this app. "
        "It will **not** work automatically on a hosted service "
        "such as Streamlit Community Cloud, since there is no "
        "local Ollama server there — a hosted LLM API would "
        "need to replace `ask_ai()` in agent.py for that "
        "deployment target."
    )

    st.markdown("---")

    if st.button("🗑️ Clear this chat", use_container_width=True):

        st.session_state.messages = []

        agent.conversation_history.clear()

        persist_current_session(sessions)

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title("🤖 My Personal Agent")

st.caption(
    "An AI agent that can use tools — calculator, date/time, "
    "web search, memory, Python execution, file operations, "
    "and multi-step task planning — to help you get things done."
)


# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "assistant" and "response" in message:

            render_response(message["response"])

        else:

            st.markdown(message["content"])


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input("Ask me anything, or give me a task...")

if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):

        st.markdown(user_input)

    with st.chat_message("assistant"):

        with st.spinner("🤖 Agent is working on it..."):

            try:

                response = agent.handle_message(user_input)

            except Exception as error:

                response = {
                    "mode": "single",
                    "tool": "CHAT",
                    "success": False,
                    "result": f"Something went wrong: {error}"
                }

        render_response(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "",
            "response": response
        }
    )

    persist_current_session(sessions)
