#!/bin/bash

# ---Initial Config---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/lib/database.sh"
DB_FILE="$SCRIPT_DIR/memory.db"
MODEL_NAME="bashbot"
WORD_LIMIT=1800

# ---Constants---
GREY=$'\e[90m'
RESET=$'\e[0m'

# ---Arg Handling---
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <your prompt here>" >&2
    exit 1
fi

#---Prompt Capture---
PROMPT="$*"


# ---Main Logic---
# 1. Fetch PREVIOUS conversation history.
CONTEXT_JSON=$(db_get_context "$WORD_LIMIT")
if [ -z "$CONTEXT_JSON" ]; then
  CONTEXT_JSON="[]"
fi

# 2. Insert the new user prompt.
db_insert "user" "$PROMPT"

# 3. Assemble the final JSON payload.
# This must be a single line. Trying to \ will terminate the stream.
MESSAGES_PAYLOAD=$(jq -n --arg prompt "$PROMPT" --argjson old_messages "$CONTEXT_JSON" '($old_messages + [{"role": "user", "content": $prompt}])')
JSON_PAYLOAD=$(jq -n --arg model "$MODEL_NAME" --argjson messages "$MESSAGES_PAYLOAD" '{model: $model, stream: true, messages: $messages}')
#echo -e "$JSON_PAYLOAD"
JQ_DISPLAY_FILTER='
      select(.done != true and .message.content != null) | 
      .message.content |
      gsub("<think>"; $grey ) |
      gsub("</think>"; $reset)
    '

# 4. Make a temp file to store the stream.
TMP_STREAM_FILE=$(mktemp)
trap 'rm -f "$TMP_STREAM_FILE"' EXIT

# 5. Send the prompt, tee the response into a temp file and parse it with jq
curl -sN -X POST --data-raw "$JSON_PAYLOAD" http://localhost:11434/api/chat | \
	tee "$TMP_STREAM_FILE" | \
	jq -r -j --unbuffered --arg grey "$GREY" --arg reset "$RESET" "$JQ_DISPLAY_FILTER"

# Final newline for the shell prompt.
printf "\n"

# 6. Parse the temp file
RAW_STREAM_OUTPUT=$(cat "$TMP_STREAM_FILE")
RAW_CONTENT=$(echo "$RAW_STREAM_OUTPUT" | jq -s -r 'map(select(.message.content).message.content) | join("")')
if [ -n "$RAW_CONTENT" ]; then
	think_start="<think>"
	think_end="</think>"
	tmp="${RAW_CONTENT##*$think_start}"
	THOUGHTS="${tmp%%$think_end*}"
	before_think="${RAW_CONTENT%%$think_start*}"
	after_think="${RAW_CONTENT##*$think_end}"
	CLEAN_CONTENT="${before_think}${after_think}"
	db_insert "assistant" "$CLEAN_CONTENT" "$THOUGHTS"
fi

# 7. Verify
# echo -e "\n---Saved to db---"
# echo -e ".headers on\n.mode table\nSELECT * FROM conversations ORDER BY id DESC LIMIT 3;" | sqlite3 "$DB_FILE"

