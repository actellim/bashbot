      
#!/bin/bash

# run.sh - A smart launcher for the Python agent.
# This script will automatically activate the virtual environment if it's
# not already active, then run the agent.

# --- Environment Check ---
# Check if the VIRTUAL_ENV variable is set.
if [ -z "$VIRTUAL_ENV" ]; then
    # It's not set. Let's try to activate it.
    VENV_ACTIVATE="venv/bin/activate"
    if [ -f "$VENV_ACTIVATE" ]; then
        echo "Virtual environment not active. Activating and re-launching..."
        # This is the magic: `exec` replaces the current script with a new
        # bash shell. That new shell first sources the activate script,
        # then re-runs this same run.sh script with all the original arguments ('$0' is the script name).
        exec bash -c "source $VENV_ACTIVATE; $0 \"\$@\""
    else
        echo "Error: Python virtual environment not found."
        echo "Please run 'python3 -m venv venv' to create it."
        exit 1
    fi
fi

# --- If we reach this point, the venv is active ---

# --- Check for Dependencies ---
if ! python3 -c "import requests; import dotenv" &> /dev/null; then
    echo "Error: Required Python packages are not installed."
    echo "Please install them:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# --- Execute the Agent ---
# "$@" passes along all command-line arguments to the Python script.
python3 agent.py "$@"

