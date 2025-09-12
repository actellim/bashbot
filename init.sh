#!/bin/bash

# init.sh - A setup script for the Bashbot Python Agent
# This script is non-interactive and safe to run multiple times.

echo "--- Starting Bashbot Setup ---"


# --- 1. Check & Install Ollama ---
if ! command -v ollama &> /dev/null
then
    echo "Ollama is not found. Installing now..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed."
fi

# --- 2. Setup Python Virtual Environment ---
echo -e "\n--- Setting up Python virtual environment in './venv' ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate the venv for the rest of this script
source venv/bin/activate

# --- 3. Install Dependencies ---
echo -e "\n--- Installing Python dependencies from requirements.txt ---"
pip install -r requirements.txt

# --- 4. Load Configuration and Pull Models ---
CONFIG_FILE=".env"
if [ -f "$CONFIG_FILE" ]; then
    set -a
    . "$CONFIG_FILE"
    set +a
    echo -e "\n--- Pulling/updating Ollama models (this may take a while)... ---"
    echo "  > Pulling main model: $BASE_MODEL"
    ollama pull "$BASE_MODEL"
    echo "  > Pulling embedding model: $EMBEDDING_MODEL"
    ollama pull "$EMBEDDING_MODEL"
fi

# --- 5. Build the Custom Agent Model ---
echo -e "\n--- Building the custom '$MODEL_NAME' model ---"
./build_model.sh

# --- 6. Initial Database Setup ---
echo -e "\n--- Setting up the SQLite database ---"
python3 db_setup.py

# In init.sh

# --- 7. Add alias to .bashrc (if it doesn't exist) ---
echo -e "\n--- Attempting to add 'bashbot' alias to ~/.bashrc ---"

# Define the alias command with the absolute path to the launcher script.
# `pwd` will resolve to the current project directory where init.sh is run.
ALIAS_COMMAND="alias bashbot='$(pwd)/run.sh'"
BASHRC_FILE="$HOME/.bashrc"

# Check if .bashrc exists and if the alias is not already in it.
if [ -f "$BASHRC_FILE" ]; then
    # Use grep -q to quietly search for the alias.
    if ! grep -q "alias bashbot=" "$BASHRC_FILE"; then
        echo "Alias not found. Adding to $BASHRC_FILE..."
        # Append the new alias to the end of the file.
        echo "" >> "$BASHRC_FILE" # Add a newline for spacing
        echo "# Alias for the Bashbot Python Agent" >> "$BASHRC_FILE"
        echo "$ALIAS_COMMAND" >> "$BASHRC_FILE"
        echo "Alias added successfully."
    else
        echo "Alias 'bashbot' already exists in $BASHRC_FILE. No action taken."
    fi
else
    echo "Could not find ~/.bashrc. Please add the following alias manually:"
    echo "  $ALIAS_COMMAND"
fi

source $BASHRC_FILE

echo -e "\n\n--- Setup Complete! ---"
echo "You can now run the agent using the launcher script: bashbot \"Your prompt here.\""

