import sqlite3
import json
from datetime import datetime, timezone

class DatabaseManager:
    """A class to manage the agent's SQLite database memory."""

    def __init__(self, db_path="memory.db"):
        """Initializes the database connection and creates the table if it doesn't exist."""
        self.db_path = db_path
        # Use a single connection for the life of the object.
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Creates the conversations table if it's not present."""
        cursor = self.conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS conversations (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           turn_id INTEGER NOT NULL,
                           timestamp TEXT NOT NULL,
                           role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool')),
                           content TEXT NOT NULL,
                           tool_calls TEXT,
                           thoughts TEXT
                           );
                       """)
        self.conn.commit()

    def get_new_turn_id(self) -> int:
        """Gets the next available turn_id for a new conversation."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(turn_id) FROM conversations")
        result = cursor.fetchone()
        # If the table is empty start at 1. Otherwise, increment the max.
        return (result[0] or 0) + 1

    def add_message(self, turn_id: int, role: str, content: str, tool_calls: list = None, thoughts: str = None):
        """Adds a new message to the conversation history."""
        timestamp = datetime.now(timezone.utc).isoformat()
        # Convert the tool_calls list to a JSON string for storage, or None.
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None

        cursor = self.conn.cursor()
        cursor.execute(
                "INSERT INTO conversations (turn_id, timestamp, role, content, tool_calls, thoughts) VALUES (?, ?, ?, ?, ?, ?)",
                (turn_id, timestamp, role, content, tool_calls_json, thoughts)
                )
        self.conn.commit()

    def get_context_messages(self, word_limit: int = 1800) -> list[dict]:
        """Fetches the most recent messages up to a specified word limit."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT role, content FROM conversations ORDER BY id ASC")
        all_messages = [dict(row) for row in cursor.fetchall()]

        word_count = 0
        context_to_return = []
        
        # Loop through the messages in reverse (from newest to oldest)
        for message in reversed(all_messages):
            content = message.get('content', '')
            num_words = len(content.split())

            # print(f"[DEBUG] Checking message: '{content[:20]}...' ({num_words} words). Current count: {word_count}")

            # Stop if adding the next message would exceed the limit,
            # but always ensure we include at least one message.
            if word_count + num_words > word_limit and len(context_to_return) > 0:
                break

            # Add the message to the *front* of our context list to keep chronological order
            context_to_return.insert(0, message)
            word_count += num_words

        # We only need the role and content for the final output
        return context_to_return

    def search_memory(self, search_term: str) -> str:
        """Searches user and assistant messages for a term and returns a formatted string."""
        cursor = self.conn.cursor()
        # The '%' wildcards are added here for the LIKE query.
        query_param = f"%{search_term}%"

        cursor.execute(
                """
                SELECT timestamp, role, content
                FROM conversations
                WHERE content LIKE ? AND role IN ('user', 'assistant')
                ORDER BY id DESC LIMIT 5;
                """,
                (query_param,)
                )
        results = cursor.fetchall()

        if not results:
            return f"No memories found matching '{search_term}'."

        # Format the results into a clean string for the LLM
        formatted_results = [
                f"--- Memory Found ---\nTimestamp: {row['timestamp']}\nRole: {row['role']}\nContent: {row['content']}"
                for row in results
                ]
        return "\n\n".join(formatted_results)

    def close(self):
        """Closes the database connection."""
        self.conn.close()

# ---Test Block---
# This only runs if you execute `database.py` directly.
if __name__ == "__main__":
    print("--- Running DatabaseManager Test ---")
    # Use an in-memory database for a clean test
    db = DatabaseManager(db_path=":memory:")

    # Test adding messages 
    print("\n1. Adding messages...")
    turn_id = db.get_new_turn_id()
    print(f"New Turn ID: {turn_id}")
    db.add_message(turn_id, "user", "Hello! My favorite color is blue.")
    db.add_message(turn_id, "assistant", "That's a great color!")
    db.add_message(turn_id, "user", "What is the capital of France?")
    sample_tool_call = [{"function": {"name": "search", "arguments": {"query": "capital of France"}}}]
    db.add_message(turn_id, "assistant", "I will search for that.", tool_calls=sample_tool_call)
    print("Messages added.")

    # Test context retrieval
    print("\n2. Testing get_context_messages (limit 15 words)...")
    context = db.get_context_messages(word_limit=15)

    print("Context retrieved:")
    print(json.dumps(context, indent=2))

    assert len(context) == 3, f"Expected 3 messages, but got {len(context)}"
    assert context[0]['content'] == "That's a great color!"
    assert context[1]['content'] == "What is the capital of France?"
    assert context[2]['content'] == "I will search for that."
    print("Context length and content are correct.")

    # Test memory search
    print("\n3. Testing search_memory...")
    search_results = db.search_memory("color")
    assert "blue" in search_results
    print("Search results:")
    print(search_results)

    # Test tool_calls
    print("\n4. Verifying tool_calls storage...")
    cursor = db.conn.cursor()
    # Fetch the last assistant message we inserted
    cursor.execute("SELECT tool_calls FROM conversations WHERE role = 'assistant' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    assert row['tool_calls'] is not None, "tool_calls column should not be NULL"
    stored_tool_calls = json.loads(row['tool_calls'])
    assert stored_tool_calls == sample_tool_call, "Stored tool_calls do not match original."
    print("tool_calls are being stored and retrieved correctly as JSON.")

    db.close()
    print("\n--- Test Complete---")
