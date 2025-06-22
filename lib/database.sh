#!/bin/bash
# lib/database.sh - A library of functions for interacting with the db.
# This library expects the DB_FILE variable to be set by the calling script.

# ---Functions---

# Inserts a new message into the conversation table.
# Usage: db_insert "role" "content" ["thoughts"] ["tool_calls"]
function db_insert() {
	#---Debug---
	# echo "---[DEBUG] Inside db_insert---"
	# echo " > Received \$1 (role): '$1'"
	# echo " > Recieved \$2 (content): '$2'"
	# echo " > Recieved \$3 (thoughts): '$3'"
	# echo " > Recieved \$4 (tool_calls): '$4'"
	# echo " > DB_FILE variable is: '$DB_FILE'"
	# echo " -----------------------------"
	#---end debug---

	# 'local' creates variables that only exist inside this function.
	local role_sql="${1//\'/\'\'}"
	local content_sql="${2//\'/\'\'}"
	# Syntax translation: If 3rd arg exists use it, else "".
	local thoughts_sql="${3//\'/\'\'}"
	local tool_calls_sql="${4//\'/\'\'}"


	local sql_statement="INSERT INTO conversations (timestamp, role, content, thoughts, tool_calls) VALUES (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), '$role_sql', '$content_sql', '$thoughts_sql', '$tool_calls_sql')" 

	# Execute the insert command using safe positional paramater bindings.
	# The '?' serve as placeholders. sqlite3 Automatically and safely subs
	# the following args into the placeholders, preventing injection.
	sqlite3 "$DB_FILE" "$sql_statement"
}

# A simple word count function
function count_words() {
	# 'wc -w' counts words.
	echo "$1" | wc -w
}

# Fetches the last N words of conversation history.
# Usage: db_get_context WORD_LIMIT
function db_get_context() {
	local word_limit="${1:-1800}" # Default to 1800 words
	local word_count=0
	local context_ids=""

	# Get all message IDs in reverse order. (Maybe we should put some sort of limit on this?)
	# 'tac' reverses the order of the lines
	local all_ids
	all_ids=$(sqlite3 "$DB_FILE" "SELECT id FROM conversations ORDER BY id ASC;" | tac)

	for id in $all_ids; do
		# Fetch the content of the current ID.
		local content
		content=$(sqlite3 "$DB_FILE" "SELECT content FROM conversations WHERE id = $id;")

		# Add the word count of this message to our total.
		word_count=$((word_count + $(count_words "$content")))
		# What are the $'s doing, exactly? They seem like a type of complier flag.

		# Add the ID to the front of our list of context ids to keep them in order.
		context_ids="$id $context_ids"

		# If we've hit the context limit, stop counting.
		# What is the -ge flag here?
		if [ "$word_count" -ge "$word_limit" ]; then
			break
		fi
	done

	# Now fetch the messages for the IDs.
	# 'tr' replaces spaces with commas. 'sed' removes the trailing comma.
	local id_list
	id_list=$(echo "$context_ids" | tr ' ' ',' | sed 's/,$//')
	# Thanks for the explination! Could you maybe break it down a bit more?
	# Like char by char?
	# My brain isn't wrinkly enough to get this first shot.
	
	# From here, process the context list to json.
	sqlite3 "$DB_FILE" -json "SELECT role, content FROM conversations WHERE id IN ($id_list) ORDER BY id ASC;"
}
