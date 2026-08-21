from pathlib import Path


# =========================================================
# WORKSPACE
# =========================================================

WORKSPACE = Path(__file__).parent / "workspace"

WORKSPACE.mkdir(exist_ok=True)


# =========================================================
# SAFE FILE PATH
# =========================================================

def get_safe_path(filename):
    filename = filename.strip()

    path = (WORKSPACE / filename).resolve()

    # Make sure the path stays inside our workspace
    if path != WORKSPACE and WORKSPACE not in path.parents:
        raise ValueError("File access outside workspace is not allowed.")

    return path


# =========================================================
# CREATE / WRITE FILE
# =========================================================

def write_file(filename, content):
    path = get_safe_path(filename)

    path.write_text(
        content,
        encoding="utf-8"
    )

    return f"File created/updated: {path.name}"


# =========================================================
# READ FILE
# =========================================================

def read_file(filename):
    path = get_safe_path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"File '{filename}' does not exist."
        )

    if not path.is_file():
        raise ValueError(
            f"'{filename}' is not a file."
        )

    return path.read_text(
        encoding="utf-8"
    )


# =========================================================
# APPEND TO FILE
# =========================================================

def append_file(filename, content):
    path = get_safe_path(filename)

    with path.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(content)

    return f"Content added to: {path.name}"