#!/bin/bash


# db_setup.sh (v2) - Added columns for thoughts and tool calls.

# ---Configuration---
DB_FILE="memory.db"

# ---Safety Check---
if [ -f "$DB_FILE" ]; then
	echo "Database file '$DB_FILE' already exists. No action taken."
	exit 0
fi

# ---Database and Table Creation---
echo "Creating database file '$DB_FILE' and setting up schema for Bashbot v0.2..."

sqlite3 "$DB_FILE" <<SQL
PRAGMA journal_mode = WAL; /* Use write-ahead logging for better concurrency. */
PRAGMA synchronous = NORMAL; /* A good balance of speed and safety? */
PRAGMA foreign_keys = ON; /* Enforce foreign key constraints. */

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    thoughts TEXT,
    tool_calls TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_role ON conversations(role);
SQL

# ---Verification---
if [ -f "$DB_FILE" ]; then
	echo "Database setup complete. File '$DB_FILE' created successfully."
	echo "Tables in database:"
	sqlite3 "$DB_FILE" ".tables"
	echo -e "\n'conversations' table columns:"
	# We use PRAGMA table_info() to get a clean list of columns.
	# -header and -column flags format the output.
	sqlite3 "$DB_FILE" -header -column  "PRAGMA table_info(conversations);"
else
	echo "Error: Database setup failed."
	exit 1
fi
