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
# PHASE 14.1 — TASK PLANNING
# =========================================================

def is_multi_step_task(text):

    text = normalize_intent_text(text)

    # -----------------------------------------------------
    # Explicit multi-step connectors
    # -----------------------------------------------------

    step_indicators = [

        r"\band\s+then\b",

        r"\bthen\b",

        r"\bafter\s+that\b",

        r"\bnext\b",

        r"\bfinally\b",

        r"\bafterwards\b",

        r"\bfollowed\s+by\b"

    ]

    for pattern in step_indicators:

        if re.search(
            pattern,
            text,
            re.I
        ):

            return True

    # -----------------------------------------------------
    # Multiple actions in one request
    # -----------------------------------------------------

    action_patterns = [

        r"\bcreate\b.*\bread\b",

        r"\bwrite\b.*\bread\b",

        r"\bcreate\b.*\bwrite\b",

        r"\bwrite\b.*\bthen\b",

        r"\bcreate\b.*\bthen\b",

        r"\bsearch\b.*\bthen\b",

        r"\bcalculate\b.*\bwrite\b",

        r"\bcalculate\b.*\bsave\b",

        r"\brun\b.*\bthen\b",

        r"\bexecute\b.*\bthen\b"

    ]

    for pattern in action_patterns:

        if re.search(
            pattern,
            text,
            re.I
        ):

            return True

    return False


def create_task_plan(user_input):

    """
    Phase 14.1:
    Break a complex request into ordered steps.

    This function only creates the plan.
    It does NOT execute the steps yet.
    """

    text = user_input.strip()

    # -----------------------------------------------------
    # Known Phase 14.1 test case
    #
    # Create a file called phase14.txt,
    # write Hello Phase 14 into it,
    # and then read it.
    # -----------------------------------------------------

    if (
        re.search(
            r"\bcreate\b.*\bfile\b",
            text,
            re.I
        )
        and
        re.search(
            r"\bwrite\b",
            text,
            re.I
        )
        and
        re.search(
            r"\bread\b",
            text,
            re.I
        )
    ):

        file_match = re.search(
            r"(?:file\s+(?:called\s+)?|called\s+)"
            r"([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)",
            text,
            re.I
        )

        filename = None

        if file_match:

            filename = file_match.group(1)

        content_match = re.search(
            r"\bwrite\s+(.+?)\s+(?:into|in|to)\s+"
            r"(?:the\s+)?(?:file\s+)?"
            r"(?:it|[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)",
            text,
            re.I
        )

        content = None

        if content_match:

            content = content_match.group(1).strip(
                "\"'"
            )

        if filename and content:

            return [

                f"Create the file {filename}",

                f"Write '{content}' into {filename}",

                f"Read {filename}"

            ]

    # -----------------------------------------------------
    # Generic planning using the AI
    # -----------------------------------------------------

    prompt = f"""
Break the user's request into a small number of clear,
ordered tasks.

This is Phase 14.1 of a personal AI agent.

IMPORTANT:

- Do NOT execute anything.
- Do NOT use tools.
- Do NOT write Python code.
- Only create the task plan.
- Each task must be one simple action.
- Keep the original intention of the user.
- Use numbered steps.
- Return ONLY the task descriptions.
- Do not add explanations.

User request:

{text}
"""

    try:

        result = ask_ai(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a task planner for a personal "
                        "AI agent. Break complex requests into "
                        "small ordered steps. Do not execute "
                        "anything."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        lines = []

        for line in result.splitlines():

            line = line.strip()

            line = re.sub(
                r"^\d+[\).\-\:]\s*",
                "",
                line
            )

            line = re.sub(
                r"^[-*]\s*",
                "",
                line
            )

            if line:

                lines.append(line)

        if lines:

            return lines

    except Exception:

        pass

    return [text]


def show_task_plan(user_input):

    print(
        "\n🤖 Agent is planning..."
    )

    plan = create_task_plan(
        user_input
    )

    print(
        "\n📋 Task plan:"
    )

    for index, step in enumerate(
        plan,
        start=1
    ):

        print(
            f"{index}. {step}"
        )

    print(
        "\nℹ️ Phase 14.1: Planning complete."
    )

    print(
        "ℹ️ Step execution will be added in Phase 14.2."
    )

    return plan


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

    for message in reversed(
        conversation_history
    ):

        if message["role"] != "user":
            continue

        message_text = (
            message["content"]
            .strip()
        )

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

    if match:

        key = match.group(1).strip()
        value = match.group(2).strip()

        return key, value

    match = re.search(
        r"remember (?:that\s+)?my\s+(.+?)\s+is\s+(.+)",
        text,
        re.I
    )

    if match:

        key = match.group(1).strip()
        value = match.group(2).strip()

        return key, value

    match = re.search(
        r"keep in mind (?:that\s+)?my\s+(.+?)\s+is\s+(.+)",
        text,
        re.I
    )

    if match:

        key = match.group(1).strip()
        value = match.group(2).strip()

        return key, value

    return None


# =========================================================
# MEMORY RECALL COMMAND
# =========================================================

def recall_command(text):

    text = text.strip()

    match = re.fullmatch(
        r"(?:what is|what's|tell me) my (.+?)[?]?",
        text,
        re.I
    )

    if match:

        return match.group(1).strip()

    patterns = [

        r"what do you remember about my (.+?)[?]?",

        r"do you remember my (.+?)[?]?",

        r"what do you know about my (.+?)[?]?",

        r"can you tell me my (.+?)[?]?"

    ]

    for pattern in patterns:

        match = re.fullmatch(
            pattern,
            text,
            re.I
        )

        if match:

            return match.group(1).strip()

    return None


# =========================================================
# PYTHON DETECTION
# =========================================================

def is_python_request(text):

    text = text.lower().strip()

    python_patterns = [

        r"^run\s+python\b",

        r"^execute\s+python\b",

        r"^use\s+python\b",

        r"^run\s+this\s+python\b",

        r"^execute\s+this\s+python\b",

        r"\brun\s+the\s+following\s+python\b",

        r"\bexecute\s+the\s+following\s+python\b",

        r"\brun\s+a\s+python\s+program\b",

        r"\bexecute\s+a\s+python\s+program\b",

        r"^run\s+this\s+code\s+in\s+python\b",

        r"^execute\s+this\s+code\s+in\s+python\b",

        r"^use\s+python\s+to\b"

    ]

    return any(
        re.search(
            pattern,
            text,
            re.I
        )
        for pattern in python_patterns
    )


# =========================================================
# FILE DETECTION
# =========================================================

def is_file_request(text):

    text = text.lower().strip()

    file_extensions = [

        ".txt",
        ".py",
        ".json",
        ".csv",
        ".md",
        ".html",
        ".css",
        ".js",
        ".java",
        ".cpp"

    ]

    has_file = any(
        extension in text
        for extension in file_extensions
    )

    if not has_file:
        return False

    file_keywords = [

        "create",
        "make",
        "write",
        "put",
        "save",
        "append",
        "read",
        "open",
        "update",
        "show",
        "display"

    ]

    return any(
        keyword in text
        for keyword in file_keywords
    )


# =========================================================
# WEB DETECTION
# =========================================================

def is_web_request(text):

    text = text.lower().strip()

    keywords = [

        "search the web",
        "search online",
        "search internet",
        "search the internet",
        "search for",
        "look up",
        "look online",
        "find online",
        "latest",
        "recent",
        "news about",
        "latest news",
        "current news",
        "what happened recently",
        "what is happening recently"

    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# FLEXIBLE CALCULATOR DETECTION
# =========================================================

def extract_calculation(text):

    expression = text.strip()

    expression = expression.rstrip(
        ".,!?;"
    ).strip()

    if re.fullmatch(
        r"[0-9+\-*/%().\s]+",
        expression
    ):

        return expression

    percentage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:of)\s*(\d+(?:\.\d+)?)",
        expression,
        re.I
    )

    if not percentage_match:

        percentage_match = re.search(
            r"(\d+(?:\.\d+)?)\s*percent\s*(?:of)\s*(\d+(?:\.\d+)?)",
            expression,
            re.I
        )

    if percentage_match:

        percentage = percentage_match.group(1)
        number = percentage_match.group(2)

        return f"({percentage} / 100) * {number}"

    prefixes = [

        "calculate ",
        "what is ",
        "what's ",
        "solve ",
        "find ",
        "compute ",
        "how much is ",
        "what is the value of ",
        "what's the value of "

    ]

    lower_expression = expression.lower()

    for prefix in prefixes:

        if lower_expression.startswith(prefix):

            expression = expression[
                len(prefix):
            ].strip()

            break

    natural = expression.lower()

    replacements = [

        (r"\bmultiplied\s+by\b", "*"),

        (r"\bmultiply\s+by\b", "*"),

        (r"\btimes\b", "*"),

        (r"\bdivided\s+by\b", "/"),

        (r"\bdivide\s+by\b", "/"),

        (r"\bplus\b", "+"),

        (r"\badd\b", "+"),

        (r"\bminus\b", "-"),

        (r"\bsubtract\b", "-"),

        (r"\bmodulo\b", "%"),

        (r"\bmod\b", "%"),

        (r"\bto\s+the\s+power\s+of\b", "**"),

        (r"\bpower\s+of\b", "**"),

        (r"\bsquared\b", "** 2"),

        (r"\bcubed\b", "** 3")

    ]

    for pattern, symbol in replacements:

        natural = re.sub(
            pattern,
            symbol,
            natural
        )

    remove_patterns = [

        r"\bcalculate\b",

        r"\bwhat is\b",

        r"\bwhat's\b",

        r"\bcan you\b",

        r"\bplease\b",

        r"\bthe answer to\b",

        r"\bthe product of\b",

        r"\bthe sum of\b",

        r"\bthe difference between\b",

        r"\bthe result of\b",

        r"\bhow much is\b",

        r"\bwhat is the value of\b",

        r"\bwhat's the value of\b"

    ]

    for pattern in remove_patterns:

        natural = re.sub(
            pattern,
            "",
            natural
        )

    natural = re.sub(
        r"(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)",
        r"\1 * \2",
        natural
    )

    natural = re.sub(
        r"(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)",
        r"\1 + \2",
        natural
    )

    natural = natural.rstrip(
        ".,!?;"
    ).strip()

    natural = natural.strip()

    if re.fullmatch(
        r"[0-9+\-*/%().\s]+",
        natural
    ):

        return natural

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
        "what day",
        "current time",
        "what time is it",
        "what is the time",
        "what's the time",
        "time now",
        "date and time",
        "date & time",
        "what is today's date",
        "what's today's date",
        "tell me today's date",
        "tell me the date",
        "tell me the time",
        "what time is it right now",
        "what is the current time",
        "what's the current time",
        "tell me the current time",
        "what is the date today",
        "what's the date today",
        "what is today's day",
        "what day is it"

    ]

    return any(
        pattern in text
        for pattern in patterns
    )


# =========================================================
# ADVANCED INTENT NORMALIZATION
# =========================================================

def normalize_intent_text(text):

    text = text.lower().strip()

    text = re.sub(
        r"[.,!?;]+$",
        "",
        text
    )

    text = text.replace(
        "×",
        "*"
    )

    text = text.replace(
        "÷",
        "/"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# ADVANCED CALCULATOR INTENT
# =========================================================

def is_advanced_calculator_request(text):

    text = normalize_intent_text(
        text
    )

    calculator_patterns = [

        r"\bwhat is the product of\b",

        r"\bwhat's the product of\b",

        r"\bcalculate the product of\b",

        r"\bfind the product of\b",

        r"\bwhat is the sum of\b",

        r"\bwhat's the sum of\b",

        r"\bcalculate the sum of\b",

        r"\bfind the sum of\b",

        r"\bwhat is the difference between\b",

        r"\bwhat's the difference between\b",

        r"\bcalculate the difference between\b",

        r"\bhow much is\b",

        r"\bwhat is the result of\b",

        r"\bwhat's the result of\b",

        r"\bcalculate the result of\b",

        r"\bwhat is the value of\b",

        r"\bwhat's the value of\b"

    ]

    return any(
        re.search(
            pattern,
            text,
            re.I
        )
        for pattern in calculator_patterns
    )


# =========================================================
# ADVANCED WEB INTENT
# =========================================================

def is_advanced_web_request(text):

    text = normalize_intent_text(
        text
    )

    patterns = [

        r"^search\s+.+",

        r"^look\s+up\s+.+",

        r"^find\s+.+\s+online$",

        r"^search\s+online\s+for\s+.+",

        r"^search\s+the\s+internet\s+for\s+.+",

        r"^can\s+you\s+search\s+.+",

        r"^can\s+you\s+look\s+up\s+.+",

        r"^find\s+the\s+latest\s+.+",

        r"^tell\s+me\s+the\s+latest\s+.+"

    ]

    return any(
        re.search(
            pattern,
            text,
            re.I
        )
        for pattern in patterns
    )


# =========================================================
# ADVANCED FILE INTENT
# =========================================================

def is_advanced_file_request(text):

    text = normalize_intent_text(
        text
    )

    file_extensions = [

        ".txt",
        ".py",
        ".json",
        ".csv",
        ".md",
        ".html",
        ".css",
        ".js",
        ".java",
        ".cpp"

    ]

    has_file = any(
        extension in text
        for extension in file_extensions
    )

    if not has_file:

        return False

    patterns = [

        r"\bshow\s+me\b",

        r"\bdisplay\b",

        r"\bopen\b",

        r"\bread\b",

        r"\bview\b",

        r"\bcreate\b",

        r"\bmake\b",

        r"\bwrite\b",

        r"\bsave\b",

        r"\bappend\b",

        r"\bupdate\b"

    ]

    return any(
        re.search(
            pattern,
            text,
            re.I
        )
        for pattern in patterns
    )


# =========================================================
# ADVANCED PYTHON INTENT
# =========================================================

def is_advanced_python_request(text):

    text = normalize_intent_text(
        text
    )

    patterns = [

        r"\brun\s+python\b",

        r"\bexecute\s+python\b",

        r"\buse\s+python\s+to\b",

        r"\brun\s+this\s+code\s+in\s+python\b",

        r"\bexecute\s+this\s+code\s+in\s+python\b",

        r"\brun\s+a\s+python\s+program\b",

        r"\bexecute\s+a\s+python\s+program\b"

    ]

    return any(
        re.search(
            pattern,
            text,
            re.I
        )
        for pattern in patterns
    )


# =========================================================
# ADVANCED MEMORY INTENT
# =========================================================

def is_advanced_memory_request(text):

    text = normalize_intent_text(
        text
    )

    remember_patterns = [

        r"^remember\s+that\b",

        r"^remember\s+my\b",

        r"^keep\s+in\s+mind\b",

        r"^save\s+this\s+in\s+memory\b",

        r"^remember\s+this\b"

    ]

    recall_patterns = [

        r"^what\s+is\s+my\b",

        r"^what's\s+my\b",

        r"^tell\s+me\s+my\b",

        r"^do\s+you\s+remember\s+my\b",

        r"^what\s+do\s+you\s+remember\s+about\s+my\b",

        r"^what\s+do\s+you\s+know\s+about\s+my\b",

        r"^can\s+you\s+tell\s+me\s+my\b"

    ]

    for pattern in remember_patterns:

        if re.search(
            pattern,
            text,
            re.I
        ):

            return True

    for pattern in recall_patterns:

        if re.search(
            pattern,
            text,
            re.I
        ):

            return True

    return False


# =========================================================
# FAST LOCAL TOOL DETECTION
# =========================================================

def fast_local_tool(user_input):

    normalized = normalize_intent_text(
        user_input
    )

    if remember_command(
        normalized
    ):

        return "MEMORY"

    if recall_command(
        normalized
    ):

        return "MEMORY"

    if is_advanced_memory_request(
        normalized
    ):

        return "MEMORY"

    if is_python_request(
        normalized
    ):

        return "PYTHON"

    if is_advanced_python_request(
        normalized
    ):

        return "PYTHON"

    if is_file_request(
        normalized
    ):

        return "FILE"

    if is_advanced_file_request(
        normalized
    ):

        return "FILE"

    if is_datetime_request(
        normalized
    ):

        return "DATETIME"

    if is_web_request(
        normalized
    ):

        return "WEB"

    if is_advanced_web_request(
        normalized
    ):

        return "WEB"

    if extract_calculation(
        normalized
    ):

        return "CALCULATOR"

    if is_advanced_calculator_request(
        normalized
    ):

        return "CALCULATOR"

    return None


# =========================================================
# AI TOOL DECISION
# =========================================================

def ai_decide_tool(user_input):

    prompt = f"""
Choose exactly ONE tool for the user's request.

Available tools:

CALCULATOR
DATETIME
WEB
MEMORY
PYTHON
FILE
CHAT

CALCULATOR:
Use for mathematical calculations.

DATETIME:
Use for current date or current time.

WEB:
Use when current or recent internet information
is required or the user explicitly asks to search online.

MEMORY:
Use for saving or recalling personal information.

PYTHON:
Use only when the user explicitly asks to run or
execute Python code.

FILE:
Use for creating, writing, reading, opening,
updating, saving, displaying, or appending files.

CHAT:
Use for normal questions, explanations,
definitions and conversation.

IMPORTANT:

1. Do not choose PYTHON merely because the question
mentions Python.

2. Do not choose CALCULATOR merely because the question
contains numbers.

3. Choose WEB when current information is required.

4. Choose FILE for local file operations.

5. Choose MEMORY for personal information.

6. Choose CHAT for explanations.

7. If the user explicitly says "run Python",
choose PYTHON.

8. If the user explicitly asks to read, create,
write, open, update, or append a file,
choose FILE.

Return ONLY one tool name.

User:
{user_input}
"""

    try:

        result = ask_ai(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a precise intent classifier. "
                        "Return only one tool name."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        ).upper().strip()

        result = re.sub(
            r"[^A-Z_]",
            "",
            result
        )

        valid_tools = {

            "CALCULATOR",
            "DATETIME",
            "WEB",
            "MEMORY",
            "PYTHON",
            "FILE",
            "CHAT"

        }

        if result in valid_tools:

            return result

    except Exception:

        pass

    return "CHAT"


# =========================================================
# AGENT DECISION
# =========================================================

def decide_tool(user_input):

    local_tool = fast_local_tool(
        user_input
    )

    if local_tool:

        return local_tool

    return ai_decide_tool(
        user_input
    )


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

        if line.strip().lower() == "end":

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
# PYTHON REQUEST PARSER
# =========================================================

def parse_python_request(user_input):

    text = user_input.strip()

    colon_match = re.search(
        r"^(?:run|execute|use)\s+python\s*:\s*(.*)$",
        text,
        re.I | re.DOTALL
    )

    if colon_match:

        code = colon_match.group(1).strip()

        if code:

            return code

    match = re.search(
        r"^(?:run|execute|use)\s+python\s+(.+)$",
        text,
        re.I | re.DOTALL
    )

    if match:

        content = match.group(1).strip()

        content = re.sub(
            r"^to\s+",
            "",
            content,
            flags=re.I
        ).strip()

        content = content.rstrip(
            ".,!?;"
        ).strip()

        number_range_match = re.search(
            r"print\s+the\s+numbers?\s+from\s+(\d+)\s+to\s+(\d+)",
            content,
            re.I
        )

        if number_range_match:

            start = number_range_match.group(1)
            end = number_range_match.group(2)

            return (
                f"for i in range({start}, {end} + 1):\n"
                f"    print(i)"
            )

        print_numbers_match = re.search(
            r"print\s+numbers?\s+from\s+(\d+)\s+to\s+(\d+)",
            content,
            re.I
        )

        if print_numbers_match:

            start = print_numbers_match.group(1)
            end = print_numbers_match.group(2)

            return (
                f"for i in range({start}, {end} + 1):\n"
                f"    print(i)"
            )

        python_indicators = [

            "print(",
            "for ",
            "while ",
            "if ",
            "def ",
            "import ",
            "from ",
            "=",
            "return ",
            "class "

        ]

        if any(
            indicator in content
            for indicator in python_indicators
        ):

            return content

    return None


# =========================================================
# FILE REQUEST PARSER
# =========================================================

def parse_file_request(user_input):

    text = user_input.strip()

    read_match = re.search(
        r"(?:read|open|show|display|view)\s+"
        r"(?:me\s+)?(?:the\s+)?(?:file\s+)?([^\s]+)",
        text,
        re.I
    )

    if read_match:

        filename = read_match.group(1).strip(
            "\"'"
        )

        filename = filename.rstrip(
            ".,!?;"
        )

        return {
            "action": "read",
            "filename": filename,
            "content": None
        }

    append_match = re.search(
        r"append\s+(.+?)\s+to\s+(?:the\s+)?file\s+([^\s]+)",
        text,
        re.I
    )

    if append_match:

        content = append_match.group(1).strip()

        filename = append_match.group(2).strip(
            "\"'"
        )

        filename = filename.rstrip(
            ".,!?;"
        )

        return {
            "action": "append",
            "filename": filename,
            "content": content
        }

    write_patterns = [

        r"(?:write|put|save)\s+(.+?)\s+"
        r"(?:in|into|to)\s+(?:the\s+)?file\s+([^\s]+)",

        r"(?:write|put|save)\s+(.+?)\s+"
        r"(?:in|into|to)\s+([^\s]+)",

        r"(?:write|put|save)\s+"
        r"([^\s]+)\s+in\s+([^\s]+)"

    ]

    for pattern in write_patterns:

        match = re.search(
            pattern,
            text,
            re.I
        )

        if match:

            content = match.group(1).strip()

            filename = match.group(2).strip(
                "\"'"
            )

            filename = filename.rstrip(
                ".,!?;"
            )

            content = content.strip(
                "\"'"
            )

            return {
                "action": "create",
                "filename": filename,
                "content": content
            }

    create_with_content = re.search(
        r"create\s+(?:a\s+)?file\s+(?:called\s+)?([^\s]+)"
        r"\s+with\s+(.+)",
        text,
        re.I
    )

    if create_with_content:

        filename = create_with_content.group(1).strip(
            "\"'"
        )

        filename = filename.rstrip(
            ".,!?;"
        )

        content = create_with_content.group(2).strip()

        return {
            "action": "create",
            "filename": filename,
            "content": content
        }

    create_patterns = [

        r"(?:can\s+you\s+)?create\s+(?:a\s+|the\s+)?file"
        r"\s+(?:called\s+)?([^\s]+)",

        r"(?:can\s+you\s+)?create\s+([^\s]+)"
        r"\s+file",

        r"(?:can\s+you\s+)?create\s+([^\s]+)"

    ]

    for pattern in create_patterns:

        match = re.search(
            pattern,
            text,
            re.I
        )

        if match:

            filename = match.group(1).strip(
                "\"'"
            )

            filename = filename.rstrip(
                ".,!?;"
            )

            return {
                "action": "create",
                "filename": filename,
                "content": ""
            }

    return None


# =========================================================
# PHASE 14.2 — SEQUENTIAL EXECUTION
# =========================================================

def execute_task_plan(plan):

    """
    Phase 14.2:
    Execute each step of a previously created task plan,
    in order, reusing the same tool dispatch logic as
    single-step requests.
    """

    print(
        "\n▶️ Executing task plan..."
    )

    for index, step in enumerate(
        plan,
        start=1
    ):

        print(
            f"\n➡️ Executing step {index}: {step}"
        )

        execute_step(
            step
        )

    print(
        "\n✅ Task plan execution complete."
    )


# =========================================================
# EXECUTE A SINGLE STEP / REQUEST
# =========================================================

def execute_step(user_input):

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

        if not expression:

            print(
                "\n❌ I couldn't understand "
                "the calculation."
            )

            return

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

        except Exception as error:

            print(
                "\n🌐 Search results:"
            )

            print(results)

            print(
                "\n❌ AI processing error:",
                error
            )

    # =====================================================
    # PYTHON
    # =====================================================

    elif tool == "PYTHON":

        code = parse_python_request(
            user_input
        )

        if not code:

            code = get_multiline_python()

        if code:

            print(
                "\n🐍 Running Python..."
            )

            try:

                result = run_python(
                    code
                )

                print(
                    "\n🔧 Python result:"
                )

                print(result)

            except Exception as error:

                print(
                    "\n❌ Python execution error:",
                    error
                )

    # =====================================================
    # MEMORY
    # =====================================================

    elif tool == "MEMORY":

        conversation_value = find_from_conversation(
            user_input
        )

        if conversation_value is not None:

            print(
                "\n🧠 From our conversation:",
                conversation_value
            )

            return

        memory_command = remember_command(
            user_input
        )

        if memory_command:

            key, value = memory_command

            try:

                result = remember(
                    key,
                    value
                )

                print(
                    "\n🧠",
                    result
                )

            except Exception as error:

                print(
                    "\n❌ Memory error:",
                    error
                )

            return

        key = recall_command(
            user_input
        )

        if key:

            try:

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

            except Exception as error:

                print(
                    "\n❌ Memory error:",
                    error
                )

    # =====================================================
    # FILE
    # =====================================================

    elif tool == "FILE":

        request = parse_file_request(
            user_input
        )

        if not request:

            print(
                "\n❌ I couldn't understand "
                "the file request."
            )

            return

        try:

            action = request["action"]

            filename = request["filename"]

            content = request["content"]

            if action == "create":

                result = write_file(
                    filename,
                    content
                )

                print(
                    "\n📄",
                    result
                )

            elif action == "read":

                result = read_file(
                    filename
                )

                print(
                    f"\n📖 {filename}:\n"
                )

                print(result)

            elif action == "append":

                result = append_file(
                    filename,
                    content
                )

                print(
                    "\n➕",
                    result
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
# PROCESS REQUEST
# =========================================================

def process_request(user_input):

    # =====================================================
    # PHASE 14.1 — TASK PLANNING
    # PHASE 14.2 — SEQUENTIAL EXECUTION
    #
    # Only complex/multi-step requests enter the planner.
    # Existing single-tool requests continue exactly as
    # before, unchanged, via execute_step().
    # =====================================================

    if is_multi_step_task(
        user_input
    ):

        plan = show_task_plan(
            user_input
        )

        execute_task_plan(
            plan
        )

        return

    execute_step(
        user_input
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