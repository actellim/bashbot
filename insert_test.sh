#!/bin/bash


#---Include the lib---
# 'source' is a Bash command that executes the contents of a file in the current shell.
# This allows access to functions from database.sh.
source "$(dirname "$0")/lib/database.sh"

#---Put the db in scope---
DB_FILE="memory.db"

#--Get the ID of the las message--
# '|| echo 0' handles the case where the table is empty.
LAST_ID=$(sqlite3 "$DB_FILE" "SELECT IFNULL(MAX(id), 0) FROM conversations")

echo "Inserting a test user message..."
# Call insert with role and content
db_insert "user" "This is my first message to the bot!"

echo "Insertinga test assistant message with thoughts..."
db_insert "assistant" "Hello! How can I help?" "The user seems friendly. I will respond in kind."

echo "Done. Let's check the db contents:"
sqlite3 "$DB_FILE" -header -column "SELECT * FROM conversations;"

echo "Cleaning up the test messages..."
sqlite3 "$DB_FILE" "DELETE FROM conversations where id > $LAST_ID;"

echo "Cleanup complete. Final DB Contents:"
sqlite3 "$DB_FILE" -header -column "SELECT * FROM conversations;"
