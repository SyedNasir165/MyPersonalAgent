import subprocess
import sys
from pathlib import Path


# =========================================================
# PYTHON WORKSPACE
# =========================================================

WORKSPACE = Path(__file__).parent / "python_workspace"

WORKSPACE.mkdir(exist_ok=True)


# =========================================================
# RUN PYTHON CODE
# =========================================================

def run_python(code, timeout=10):

    script_path = WORKSPACE / "agent_script.py"

    try:

        # Write the Python code into the workspace
        script_path.write_text(
            code,
            encoding="utf-8"
        )

        # Run the script using the same Python installation
        result = subprocess.run(
            [
                sys.executable,
                str(script_path)
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0:

            return (
                "Python execution failed:\n"
                + error
            )

        if output:

            return output

        return "Python executed successfully with no output."

    except subprocess.TimeoutExpired:

        return "Python execution stopped: time limit exceeded."

    except Exception as error:

        return f"Python execution error: {error}"