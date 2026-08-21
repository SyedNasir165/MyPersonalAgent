"""
Streamlit UI for My Personal Agent.

This file is a thin presentation layer only. All agent logic,
tool routing, task planning, and execution live in agent.py
and its supporting modules (file_tools.py, python_tool.py,
memory.py). This file never re-implements any of that logic —
it only calls agent.handle_message() and renders the result.
"""

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
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

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

    if st.button("🗑️ Clear conversation", use_container_width=True):

        st.session_state.messages = []

        agent.conversation_history.clear()

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
