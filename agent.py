import ast
import operator
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import ollama

from file_tools import write_file, read_file, append_file
from python_tool import run_python
from memory import remember, recall


# =========================================================
# SHORT-TERM CONVERSATION MEMORY
# =========================================================

conversation_history = []


# =========================================================
# CALCULATOR
# =========================================================

def calculator(expression):

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }

    def calculate(node):

        if isinstance(node, ast.Constant) and isinstance(
            node.value,
            (int, float)
        ):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in operators:

            left = calculate(node.left)
            right = calculate(node.right)

            return operators[type(node.op)](
                left,
                right
            )

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op,
            (ast.UAdd, ast.USub)
        ):

            value = calculate(node.operand)

            if isinstance(node.op, ast.UAdd):
                return value

            return -value

        raise ValueError("Invalid calculation")

    tree = ast.parse(
        expression,
        mode="eval"
    )

    return calculate(tree.body)


# =========================================================
# DATE & TIME
# =========================================================

def get_datetime():

    return datetime.now().strftime(
        "%A, %d/%m/%Y, %I:%M:%S %p"
    )


# =========================================================
# WEB SEARCH
# =========================================================

def web_search(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            params={"q": query},
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for result in soup.select(".result")[:5]:

            title_element = result.select_one(
                ".result__title"
            )

            snippet_element = result.select_one(
                ".result__snippet"
            )

            if not title_element:
                continue

            title = title_element.get_text(
                " ",
                strip=True
            )

            snippet = ""

            if snippet_element:

                snippet = snippet_element.get_text(
                    " ",
                    strip=True
                )

            results.append(
                f"{title} - {snippet}"
            )

        if not results:

            return "No web search results found."

        return "\n".join(results)

    except Exception as error:

        return f"Web search failed: {error}"


# =========================================================
# AI
# =========================================================

def ask_ai(messages):

    response = ollama.chat(
        model="phi3:mini",
        messages=messages
    )

    return response["message"]["content"].strip()


# =========================================================
# SHORT-TERM CONVERSATION
# =========================================================

def chat_with_memory(user_input):

    conversation_history.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful personal AI assistant. "
                "Use the conversation history to understand "
                "follow-up questions. Answer clearly and "
                "concisely."
            )
        }
    ]

    messages.extend(
        conversation_history
    )

    answer = ask_ai(
        messages
    )

    conversation_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer


# =========================================================
# FIND INFORMATION FROM CURRENT CONVERSATION
# =========================================================

def find_from_conversation(question):

    question_lower = question.lower().strip()

    # -----------------------------------------------
    # Generic "my X" question
    # -----------------------------------------------

    match_question = re.fullmatch(
        r"(?:what is|what's|tell me) my (.+?)[?]?",
        question_lower
    )

    if not match_question:

        return None

    requested_key = (
        match_question.group(1)
        .strip()
        .lower()
    )

    # Search recent user messages

    for message in reversed(
        conversation_history
    ):

        if message["role"] != "user":
            continue

        message_text = (
            message["content"]
            .strip()
        )

        # Pattern:
        # my favorite language is Python
        pattern = (
            r"\bmy\s+"
            + re.escape(requested_key)
            + r"\s+is\s+(.+)"
        )

        match = re.search(
            pattern,
            message_text,
            re.I
        )

        if match:

            return match.group(1).strip()

        # Pattern:
        # my name is Nasir
        if requested_key == "name":

            match = re.search(
                r"\bmy\s+name\s+is\s+(.+)",
                message_text,
                re.I
            )

            if match:

                return match.group(1).strip()

    return None


# =========================================================
# MEMORY COMMAND
# =========================================================

def remember_command(text):

    match = re.search(
        r"remember that (.+?) is (.+)",
        text,
        re.I
    )

    if not match:

        return None

    key = match.group(1).strip()
    value = match.group(2).strip()

    return key, value


# =========================================================
# MEMORY RECALL COMMAND
# =========================================================

def recall_command(text):

    match = re.fullmatch(
        r"(?:what is|what's|tell me) my (.+?)[?]?",
        text.strip(),
        re.I
    )

    if not match:

        return None

    return match.group(1).strip()


# =========================================================
# PYTHON DETECTION
# =========================================================

def is_python_request(text):

    text = text.lower().strip()

    return (
        text.startswith("run python")
        or
        text.startswith("execute python")
        or
        text.startswith("use python")
    )


# =========================================================
# FILE DETECTION
# =========================================================

def is_file_request(text):

    text = text.lower()

    keywords = [
        "create a file",
        "create file",
        "read file",
        "open file",
        "append to file"
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# WEB DETECTION
# =========================================================

def is_web_request(text):

    text = text.lower()

    keywords = [
        "search the web",
        "search online",
        "search internet",
        "search for",
        "look up",
        "latest",
        "recent",
        "news about"
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# CALCULATION DETECTION
# =========================================================

def extract_calculation(text):

    expression = text.strip()

    prefixes = [
        "calculate ",
        "what is ",
        "what's ",
        "solve "
    ]

    lower_expression = expression.lower()

    for prefix in prefixes:

        if lower_expression.startswith(prefix):

            expression = expression[
                len(prefix):
            ].strip()

            break

    if re.fullmatch(
        r"[0-9+\-*/%().\s]+",
        expression
    ):

        return expression

    return None


# =========================================================
# DATE/TIME DETECTION
# =========================================================

def is_datetime_request(text):

    text = text.lower().strip()

    patterns = [
        "today",
        "today date",
        "today's date",
        "todays date",
        "current date",
        "what date",
        "what day is today",
        "current time",
        "what time is it",
        "what is the time",
        "what's the time",
        "time now",
        "date and time",
        "date & time"
    ]

    return any(
        pattern in text
        for pattern in patterns
    )


# =========================================================
# AGENT DECISION
# =========================================================

def decide_tool(user_input):

    if extract_calculation(user_input):

        return "CALCULATOR"

    if is_datetime_request(user_input):

        return "DATETIME"

    if remember_command(user_input):

        return "MEMORY"

    if recall_command(user_input):

        return "MEMORY"

    if is_python_request(user_input):

        return "PYTHON"

    if is_file_request(user_input):

        return "FILE"

    if is_web_request(user_input):

        return "WEB"

    prompt = f"""
Choose exactly ONE:

WEB
CHAT

WEB means the question needs current internet information.
CHAT means normal conversation or general knowledge.

Return only WEB or CHAT.

User:
{user_input}
"""

    try:

        result = ask_ai(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a simple "
                        "tool classifier."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        ).upper()

        if "WEB" in result:

            return "WEB"

    except Exception:

        pass

    return "CHAT"


# =========================================================
# MULTI-LINE PYTHON
# =========================================================

def get_multiline_python():

    print()
    print("🐍 Enter Python code.")
    print("Type END on a new line when finished.")
    print()

    lines = []

    while True:

        try:

            line = input("Python: ")

        except (KeyboardInterrupt, EOFError):

            print(
                "\n❌ Python input cancelled."
            )

            return None

        if line.strip() == "END":

            break

        lines.append(line)

    code = "\n".join(lines)

    if not code.strip():

        print(
            "\n❌ No Python code entered."
        )

        return None

    return code


# =========================================================
# PROCESS REQUEST
# =========================================================

def process_request(user_input):

    print(
        "\n🤖 Agent is deciding..."
    )

    tool = decide_tool(
        user_input
    )

    print(
        f"🔧 Selected tool: {tool}"
    )


    # =====================================================
    # CALCULATOR
    # =====================================================

    if tool == "CALCULATOR":

        expression = extract_calculation(
            user_input
        )

        try:

            result = calculator(
                expression
            )

            print(
                "\n🧮 Calculator result:",
                result
            )

        except Exception as error:

            print(
                "\n❌ Calculator error:",
                error
            )


    # =====================================================
    # DATE & TIME
    # =====================================================

    elif tool == "DATETIME":

        result = get_datetime()

        print(
            "\n🕐 Date & Time:",
            result
        )


    # =====================================================
    # WEB
    # =====================================================

    elif tool == "WEB":

        print(
            "\n🌐 Searching the web..."
        )

        results = web_search(
            user_input
        )

        try:

            answer = chat_with_memory(
                f"""
Answer my question using these web results.

Question:
{user_input}

Web results:
{results}
"""
            )

            print(
                "\nAI:",
                answer
            )

        except Exception:

            print(
                "\n🌐 Search results:"
            )

            print(results)


    # =====================================================
    # PYTHON
    # =====================================================

    elif tool == "PYTHON":

        match = re.search(
            r"^(?:run|execute)\s+python\s*:?\s*(.*)$",
            user_input,
            re.I | re.DOTALL
        )

        if match and match.group(1).strip():

            code = match.group(1).strip()

        else:

            code = get_multiline_python()

        if code:

            print(
                "\n🐍 Running Python..."
            )

            result = run_python(
                code
            )

            print(
                "\n🔧 Python result:"
            )

            print(result)


    # =====================================================
    # MEMORY
    # =====================================================

    elif tool == "MEMORY":

        # -------------------------------------------------
        # First: check short-term conversation
        # -------------------------------------------------

        conversation_value = find_from_conversation(
            user_input
        )

        if conversation_value is not None:

            print(
                "\n🧠 From our conversation:",
                conversation_value
            )

            return


        # -------------------------------------------------
        # Second: check explicit remember command
        # -------------------------------------------------

        memory_command = remember_command(
            user_input
        )

        if memory_command:

            key, value = memory_command

            result = remember(
                key,
                value
            )

            print(
                "\n🧠",
                result
            )

            return


        # -------------------------------------------------
        # Third: check long-term memory
        # -------------------------------------------------

        key = recall_command(
            user_input
        )

        if key:

            value = recall(
                key
            )

            if value is not None:

                print(
                    f"\n🧠 I remember that "
                    f"{key} is {value}."
                )

            else:

                print(
                    f"\n🧠 I don't have "
                    f"'{key}' in my memory."
                )


    # =====================================================
    # FILE
    # =====================================================

    elif tool == "FILE":

        create_match = re.search(
            r"create (?:a )?file called ([\w.\-]+) with (.+)",
            user_input,
            re.I
        )

        read_match = re.search(
            r"read (?:the )?file ([\w.\-]+)",
            user_input,
            re.I
        )

        append_match = re.search(
            r"append (.+) to ([\w.\-]+)",
            user_input,
            re.I
        )

        try:

            if create_match:

                filename = create_match.group(1)
                content = create_match.group(2)

                result = write_file(
                    filename,
                    content
                )

                print(
                    "\n📄",
                    result
                )

            elif read_match:

                filename = read_match.group(1)

                result = read_file(
                    filename
                )

                print(
                    f"\n📖 {filename}:\n"
                )

                print(result)

            elif append_match:

                content = append_match.group(1)
                filename = append_match.group(2)

                result = append_file(
                    filename,
                    content
                )

                print(
                    "\n➕",
                    result
                )

            else:

                print(
                    "\n❌ I couldn't understand "
                    "the file request."
                )

        except Exception as error:

            print(
                "\n❌ File error:",
                error
            )


    # =====================================================
    # NORMAL CHAT
    # =====================================================

    else:

        try:

            answer = chat_with_memory(
                user_input
            )

            print(
                "\nAI:",
                answer
            )

        except Exception as error:

            print(
                "\n❌ AI error:",
                error
            )


# =========================================================
# CONTINUOUS AGENT LOOP
# =========================================================

print()
print("=" * 55)
print("🤖 My Personal Agent")
print("=" * 55)
print("Type 'exit' or 'quit' to stop.")
print("=" * 55)

while True:

    try:

        user_input = input(
            "\nYou: "
        ).strip()

    except (KeyboardInterrupt, EOFError):

        print(
            "\n\n👋 Agent stopped."
        )

        break

    if not user_input:

        continue

    if user_input.lower() in {
        "exit",
        "quit"
    }:

        print(
            "\n👋 Goodbye!"
        )

        break

    process_request(
        user_input
    )