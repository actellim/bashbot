#!/bin/bash


# A script for testing db_get_context()

#---Include the Library---
source "$(dirname "$0")/lib/database.sh"
DB_FILE="memory.db"

#---Setup: Clear the DB and add known data---
echo "---Setting up test env---"
# Clear the conversation table
sqlite3 "$DB_FILE" "DELETE FROM conversations;"

echo "Inserting test data..."
# word count: 10
db_insert "user" "This is the first message, it has exactly ten words."
# word count: 4
db_insert "assistant" "Okay, I understand that."
# word count: 10
db_insert "user" "This is the third message, it also has ten words."
# word count: 5
db_insert "assistant" "Great, thank you for clarifying."

echo -e "\n---Current db state (4 messages, 29 words total)---"
sqlite3 "$DB_FILE" -header -column "SELECT id, role, content FROM conversations;"

#---Test Case 1: Word limit is high---
CONTEXT_JSON=$(db_get_context 100)
echo "Returned json:"
# Pipe the json through jq for pretty-print
echo "$CONTEXT_JSON" | jq

#---Test Case 2: Word limit 12---
CONTEXT_JSON=$(db_get_context 12)
echo "Returned json:"
echo "$CONTEXT_JSON" | jq

#---Test Case 3: default---
CONTEXT_JSON=$(db_get_context)
echo "Returned json:"
echo "$CONTEXT_JSON" | jq

#--Teardown & Cleanup---
echo -e "\n---Tearing down test env---"
sqlite3 "$DB_FILE" "DELETE FROM conversations;"
echo "Database cleared."
