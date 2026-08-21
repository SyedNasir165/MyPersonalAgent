import json
import re
from pathlib import Path


# =========================================================
# MEMORY FILE
# =========================================================

MEMORY_FILE = Path(__file__).parent / "memory.json"


# =========================================================
# NORMALIZE MEMORY KEY
# =========================================================

def normalize_key(key):

    key = key.lower().strip()

    # Remove "my"
    key = re.sub(
        r"^my\s+",
        "",
        key
    )

    # Convert underscores to spaces
    key = key.replace("_", " ")

    # Remove extra spaces
    key = re.sub(
        r"\s+",
        " ",
        key
    )

    return key.strip()


# =========================================================
# LOAD MEMORY
# =========================================================

def load_memory():

    if not MEMORY_FILE.exists():
        return {}

    try:

        with MEMORY_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {}


# =========================================================
# SAVE MEMORY
# =========================================================

def save_memory(memory):

    with MEMORY_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            memory,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# REMEMBER
# =========================================================

def remember(key, value):

    memory = load_memory()

    normalized_key = normalize_key(key)

    memory[normalized_key] = value

    save_memory(memory)

    return (
        f"I'll remember that "
        f"{normalized_key} is {value}."
    )


# =========================================================
# RECALL
# =========================================================

def recall(key):

    memory = load_memory()

    normalized_key = normalize_key(key)

    # Direct lookup
    if normalized_key in memory:

        return memory[normalized_key]

    # Check older memory entries
    for stored_key, value in memory.items():

        if normalize_key(stored_key) == normalized_key:

            return value

    return None


# =========================================================
# GET ALL MEMORY
# =========================================================

def get_all_memory():

    return load_memory()