#!/bin/bash

# stream_capture.sh - A diagnostic tool to capture the raw
# output stream from the /api/chat endpoint.

# ---Initial Config---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/lib/database.sh"
DB_FILE="$SCRIPT_DIR/memory.db"
MODEL_NAME="bashbot"
# We'll use a smaller context for this test to keep it simple.
WORD_LIMIT=200

# --- User Prompt ---
# Use a default prompt or take one from the command line.
PROMPT="${1:-Tell me a short, two-line joke.}"
echo "--- Using Prompt: \"$PROMPT\" ---"

# --- Main Logic ---

# 1. Fetch some previous history to make the test realistic.
CONTEXT_JSON=$(db_get_context "$WORD_LIMIT")
if [ -z "$CONTEXT_JSON" ]; then
  CONTEXT_JSON="[]"
fi
# Note: We are NOT inserting the new prompt into the DB for this simple test.

# 2. Assemble the JSON payload.
JSON_PAYLOAD=$(jq -n --arg model "$MODEL_NAME" --arg prompt "$PROMPT" --argjson old_messages "$CONTEXT_JSON" '($old_messages + [{"role": "user", "content": $prompt}]) | {model: $model, stream: true, messages: .}')

# 3. The Capture Command
LOG_FILE="raw_chat_stream.log"
echo "--- Capturing stream to $LOG_FILE ---"
echo "--- Live (messy) output will appear below ---"

# We pipe the curl output to 'tee' to clone the stream.
# One copy goes to the log file, the other goes to the terminal (stdout).
curl -sN -X POST --data-raw "$JSON_PAYLOAD" http://localhost:11434/api/chat | tee "$LOG_FILE"

echo -e "\n\n--- Capture Complete ---"
echo "Analyze the clean log file with: cat $LOG_FILE"
echo "Or for a pretty view: cat $LOG_FILE | jq"
