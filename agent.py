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

    python_patterns = [

        r"^run\s+python\b",
        r"^execute\s+python\b",
        r"^use\s+python\b",
        r"^run\s+this\s+python\b",
        r"^execute\s+this\s+python\b",
        r"\brun\s+the\s+following\s+python\b",
        r"\bexecute\s+the\s+following\s+python\b",
        r"\brun\s+a\s+python\s+program\b",
        r"\bexecute\s+a\s+python\s+program\b"

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
        "update"
    ]

    return any(
        keyword in text
        for keyword in file_keywords
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
# FLEXIBLE CALCULATOR DETECTION
# =========================================================

def extract_calculation(text):

    expression = text.strip()

    # -----------------------------------------------------
    # Remove common sentence-ending punctuation.
    #
    # Example:
    # What is 25 multiplied by 40?
    #
    # The question mark should not prevent the expression
    # from being recognized.
    # -----------------------------------------------------

    expression = expression.rstrip(
        ".,!?;"
    ).strip()

    # -----------------------------------------------------
    # DIRECT MATHEMATICAL EXPRESSION
    # -----------------------------------------------------

    if re.fullmatch(
        r"[0-9+\-*/%().\s]+",
        expression
    ):

        return expression

    # -----------------------------------------------------
    # PERCENTAGE CALCULATIONS
    #
    # Examples:
    # 15% of 200
    # What is 15 percent of 200?
    # Calculate 25% of 800
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # COMMON CALCULATION PREFIXES
    # -----------------------------------------------------

    prefixes = [
        "calculate ",
        "what is ",
        "what's ",
        "solve ",
        "find ",
        "compute "
    ]

    lower_expression = expression.lower()

    for prefix in prefixes:

        if lower_expression.startswith(prefix):

            expression = expression[
                len(prefix):
            ].strip()

            break

    # -----------------------------------------------------
    # DIRECT EXPRESSION AFTER PREFIX
    # -----------------------------------------------------

    if re.fullmatch(
        r"[0-9+\-*/%().\s]+",
        expression
    ):

        return expression

    # -----------------------------------------------------
    # NATURAL LANGUAGE OPERATIONS
    # -----------------------------------------------------

    natural = expression.lower()

    replacements = [

        (r"\bmultiplied\s+by\b", "*"),
        (r"\btimes\b", "*"),
        (r"\bdivided\s+by\b", "/"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\bmodulo\b", "%"),
        (r"\bmod\b", "%"),
        (r"\bto\s+the\s+power\s+of\b", "**"),
        (r"\bpower\s+of\b", "**")

    ]

    for pattern, symbol in replacements:

        natural = re.sub(
            pattern,
            symbol,
            natural
        )

    natural = re.sub(
        r"\bcalculate\b",
        "",
        natural
    )

    natural = re.sub(
        r"\bwhat is\b",
        "",
        natural
    )

    natural = re.sub(
        r"\bwhat's\b",
        "",
        natural
    )

    natural = re.sub(
        r"\bcan you\b",
        "",
        natural
    )

    natural = re.sub(
        r"\bplease\b",
        "",
        natural
    )

    natural = re.sub(
        r"\bthe answer to\b",
        "",
        natural
    )

    # -----------------------------------------------------
    # Remove punctuation again after natural-language
    # conversion.
    # -----------------------------------------------------

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
        "tell me the time"

    ]

    return any(
        pattern in text
        for pattern in patterns
    )


# =========================================================
# FAST LOCAL TOOL DETECTION
# =========================================================

def fast_local_tool(user_input):

    # -----------------------------------------------------
    # Explicit memory commands
    # -----------------------------------------------------

    if remember_command(
        user_input
    ):

        return "MEMORY"

    if recall_command(
        user_input
    ):

        return "MEMORY"

    # -----------------------------------------------------
    # Explicit Python requests
    # -----------------------------------------------------

    if is_python_request(
        user_input
    ):

        return "PYTHON"

    # -----------------------------------------------------
    # File requests
    # -----------------------------------------------------

    if is_file_request(
        user_input
    ):

        return "FILE"

    # -----------------------------------------------------
    # Date and time
    # -----------------------------------------------------

    if is_datetime_request(
        user_input
    ):

        return "DATETIME"

    # -----------------------------------------------------
    # Web requests
    # -----------------------------------------------------

    if is_web_request(
        user_input
    ):

        return "WEB"

    # -----------------------------------------------------
    # Calculator
    # -----------------------------------------------------

    if extract_calculation(
        user_input
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

=========================================================
CALCULATOR
=========================================================

Choose CALCULATOR when the user wants a mathematical
calculation or numerical answer.

Examples:

"What is 25 multiplied by 40?"
"Calculate 15% of 200."
"What's 88 + 7?"
"How much is 25 times 8?"
"Find 20 percent of 500."

Do NOT choose CALCULATOR simply because a question
contains a number.

=========================================================
DATETIME
=========================================================

Choose DATETIME when the user asks for the current date,
current day, or current time.

Examples:

"What time is it?"
"What is today's date?"
"What day is today?"
"Tell me the current time."

=========================================================
WEB
=========================================================

Choose WEB when the user explicitly asks to search online,
search the web, look something up, or needs current/recent
internet information.

Examples:

"Search the web for the latest Python news."
"Look up the latest AI news."
"Search online for Python 3.15."
"What happened recently in AI?"

=========================================================
MEMORY
=========================================================

Choose MEMORY when the user wants to save or recall
personal information.

Examples:

"Remember that my favorite editor is VS Code."
"What is my favorite editor?"
"Tell me what you remember about my favorite editor."

=========================================================
PYTHON
=========================================================

Choose PYTHON only when the user explicitly asks to
run or execute Python code.

Examples:

"Run Python to print numbers from 1 to 5."
"Execute this Python code."
"Use Python to calculate something."

Do NOT choose PYTHON for a normal programming question.

For example:

"What is recursion?"
"What is a Python function?"
"Explain recursion."

These are CHAT unless the user explicitly asks you to
execute Python code.

=========================================================
FILE
=========================================================

Choose FILE when the user wants to create, write, read,
open, update, save, or append a local file.

Examples:

"Create a file called test.txt."
"Read phase13.txt."
"Write Hello into notes.txt."
"Append this text to notes.txt."

=========================================================
CHAT
=========================================================

Choose CHAT for normal questions, explanations,
definitions, programming concepts, conversation, and
general knowledge that does not require a tool.

Examples:

"What is recursion?"
"Explain linked lists."
"What is Python?"
"How does binary search work?"

=========================================================
IMPORTANT RULES
=========================================================

1. Do not choose PYTHON merely because the question
   mentions Python.

2. Do not choose CALCULATOR merely because the question
   contains numbers.

3. Choose WEB when current or recent internet information
   is required.

4. Choose FILE when a local file operation is requested.

5. Choose MEMORY for personal information being stored
   or recalled.

6. Choose CHAT for explanations and general questions.

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
                        "Classify the user's request into exactly "
                        "one available tool. Never return an "
                        "explanation. Return only the tool name."
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

    # -----------------------------------------------------
    # Explicit Python code after colon
    # -----------------------------------------------------

    colon_match = re.search(
        r"^(?:run|execute|use)\s+python\s*:\s*(.*)$",
        text,
        re.I | re.DOTALL
    )

    if colon_match:

        code = colon_match.group(1).strip()

        if code:

            return code

    # -----------------------------------------------------
    # Python code after "run python"
    # -----------------------------------------------------

    match = re.search(
        r"^(?:run|execute|use)\s+python\s+(.+)$",
        text,
        re.I | re.DOTALL
    )

    if match:

        content = match.group(1).strip()

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

        # -------------------------------------------------
        # Natural-language Python request
        # -------------------------------------------------

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

    return None


# =========================================================
# FILE REQUEST PARSER
# =========================================================

def parse_file_request(user_input):

    text = user_input.strip()

    # -----------------------------------------------------
    # READ FILE
    #
    # Supports:
    #
    # read file phase13.txt
    # read phase13.txt
    # open file phase13.txt
    # open phase13.txt
    # -----------------------------------------------------

    read_match = re.search(
        r"(?:read|open)\s+(?:the\s+)?(?:file\s+)?([^\s]+)",
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

    # -----------------------------------------------------
    # APPEND TO FILE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # WRITE / SAVE / PUT CONTENT INTO FILE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE FILE WITH CONTENT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE EMPTY FILE
    # -----------------------------------------------------

    create_patterns = [

        r"(?:can\s+you\s+)?create\s+(?:a\s+)?file"
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