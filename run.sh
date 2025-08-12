#!/bin/bash
# run.sh - A smart launcher for the Python agent.

# Get the directory where THIS script is located.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Environment Check ---
if [ -z "$VIRTUAL_ENV" ] || [ ! -d "$VIRTUAL_ENV" ]; then
    VENV_ACTIVATE="$SCRIPT_DIR/venv/bin/activate"
    if [ -f "$VENV_ACTIVATE" ]; then
        echo "Virtual environment not active. Activating..."
        source "$VENV_ACTIVATE"
    else
        echo "Error: Python virtual environment not found in '$SCRIPT_DIR/venv'."
        echo "Please run 'python3 -m venv venv' in the project directory."
        exit 1
    fi
fi

# --- Check for Dependencies ---
if ! python3 -c "import requests; import dotenv" &> /dev/null; then
    echo "Error: Required Python packages are not installed in this venv."
    echo "Please activate the venv ('source venv/bin/activate') and run:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# --- Execute the Agent ---
# Run the agent.py script, which is in the same directory as this launcher.
python3 "$SCRIPT_DIR/agent.py" "$@"
