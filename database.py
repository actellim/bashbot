import os
import sqlite3
import json
from datetime import datetime, timezone
import numpy as np
import sqlite_vec
from embedding import get_embedding
from config import EMBEDDING_DIMENSION, VECTOR_SIMILARITY_THRESHOLD

class DatabaseManager:
    """A class to manage the agent's SQLite database memory, including vector search."""

    def __init__(self, db_path="memory.db"):
        """Initializes the database connection and creates the table if it doesn't exist."""
        self.db_path = db_path
        # Use a single connection for the life of the object.
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Load for sqlite-vec
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

        self._create_tables()

    def _create_tables(self):
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
                           thoughts TEXT,
                           embedding BLOB
                           );
                       """)
        self.conn.commit()

        cursor.execute(f"""
                       CREATE VIRTUAL TABLE IF NOT EXISTS vec_conversations
                       USING vec0(embedding float[{EMBEDDING_DIMENSION}]);
                       """)
        self.conn.commit()
        print("[DB_SETUP] Tables and vector search virtual table are ready.")

    def get_new_turn_id(self) -> int:
        """Gets the next available turn_id for a new conversation."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(turn_id) FROM conversations")
        result = cursor.fetchone()
        # If the table is empty start at 1. Otherwise, increment the max.
        return (result[0] or 0) + 1

    def add_message(self, turn_id: int, role: str, content: str, tool_calls: list = None, thoughts: str = None):
        """
        Adds a new message to the conversation history, and automatically generates and stores its embedding.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        # Convert the tool_calls list to a JSON string for storage, or None.
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None

        #---Embedding Pipeline---
        embedding_vector = None
        if role in ['user', 'assistant'] and content:
            embedding_vector = get_embedding(content)
        embedding_blob = np.array(embedding_vector, dtype=np.float32).tobytes() if embedding_vector else None
        
        cursor = self.conn.cursor()
        cursor.execute(
                "INSERT INTO conversations (turn_id, timestamp, role, content, tool_calls, thoughts, embedding) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (turn_id, timestamp, role, content, tool_calls_json, thoughts, embedding_blob)
                )
        last_id = cursor.lastrowid
        if embedding_blob:
            cursor.execute(
                    "INSERT INTO vec_conversations(rowid, embedding) VALUES (?, ?)",
                    (last_id, embedding_blob)
                    )

        self.conn.commit()

    def find_similar_memories(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        """
        Finds the top_k most similar messages in the database to a given query vector,
        and returns them in order of similarity.
        This version uses a subquery to avoid the sqlite3.OperationalError.
        """
        if query_vector is None or query_vector.size == 0:
            return []

        cursor = self.conn.cursor()

        # This query uses a JOIN against a subquery to find the k-nearest neighbors.
        # This is the recommended approach for using LIMIT with sqlite-vec.
        cursor.execute(
            """
            SELECT
                c.id, c.turn_id, c.timestamp, c.role, c.content, c.tool_calls, c.thoughts
            FROM conversations c
            JOIN (
                SELECT rowid, distance
                FROM vec_conversations
                WHERE embedding MATCH ?
                AND distance < ?
                ORDER BY distance
                LIMIT ?
            ) AS similar_rows ON c.id = similar_rows.rowid
            ORDER BY similar_rows.distance;
            """,
            (query_vector.tobytes(), VECTOR_SIMILARITY_THRESHOLD, top_k)
        )
        
        results = [dict(row) for row in cursor.fetchall()]
        return results

    def get_context_messages(self, word_limit: int = 1800) -> list[dict]:
        """
        Fetches the most recent messages up to a specified word limit.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT role, content, tool_calls, thoughts FROM conversations ORDER BY id ASC")
        all_rows = cursor.fetchall()

        word_count = 0
        context_to_return = []
        
        # Loop through the messages in reverse (from newest to oldest)
        for row in reversed(all_rows):
            message = {"role": row['role'], "content": row['content']}
            num_words = 0
            
            # Add thoughts to content if they exist
            if row['thoughts']:
                thoughts = {"thoughts": row['thoughts']}
                message['content'] = f"{thoughts['thoughts']}\n{message['content']}"
            num_words += len(message['content'].split())

            # Parse tool calls
            if row['tool_calls']:
                message['tool_calls'] = json.loads(row['tool_calls'])
            num_words += len(message['tool_calls'].split())

            # Check word count after adding thoughts

            # Stop if adding the next message would exceed the limit,
            # but always ensure we include at least one message.
            if word_count + num_words > word_limit and len(context_to_return) > 0:
                break

            # Add the message to the *front* of our context list to keep chronological order
            context_to_return.insert(0, message)
            word_count += num_words

        # We only need the role and content for the final output
        return context_to_return

    def get_messages_for_turn(self, turn_id: int) -> list[dict]:
        """
        Fetches all messages (user, assistant, tool) for a specific turn_id,
        ensuring they are in chronological order and correctly formatted for the API.
        """
        cursor = self.conn.cursor()
        cursor.execute(
                """
                SELECT role, content, tool_calls, thoughts 
                FROM conversations
                WHERE turn_id = ?
                ORDER BY id ASC
                """,
                (turn_id,)
                )

        messages = []
        for row in cursor.fetchall():
            message = {"role": row['role'], "content": row['content']}

            if row['thoughts']:
                message['content'] = f"<think>{row['thoughts']}</think>\n{row['content']}"

            if row['tool_calls']:
                message['tool_calls'] = json.loads(row['tool_calls'])

            messages.append(message)
        return messages


    def get_long_term_history(self, current_turn_id: int, limit: int = 10) -> list[dict]:
        """
        Gets the long-term history from all PREVIOUS turns.
        For now, this fetches the last few chronological messages.
        """
        cursor = self.conn.cursor()
        cursor.execute(
                """
                SELECT role, content, tool_calls, thoughts
                FROM conversations
                WHERE turn_id < ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (current_turn_id, limit)
                )

        messages = []
        for row in reversed(cursor.fetchall()):
            message = {"role": row['role'], "content": row['content']}
            if row['thoughts']:
                message['content'] = f"<think>{row['thoughts']}</think>\n{row['content']}"
            if row['tool_calls']:
                message['tool_calls'] = json.loads(row['tool_calls'])
            messages.append(message)
        return messages


    def search_memory(self, search_term: str) -> str:
        """Searches user and assistant messages for a term and returns a formatted string."""
        cursor = self.conn.cursor()
        # The '%' wildcards are added here for the LIKE query.
        query_param = f"%{search_term}%"

        cursor.execute(
                """
                SELECT turn_id, timestamp, role, content
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
                f"--- Memory Found ---\nTurn ID: {row['turn_id']}\nTimestamp: {row['timestamp']}\nRole: {row['role']}\nContent: {row['content']}"
                for row in results
                ]
        return "\n\n".join(formatted_results)

    def close(self):
        """Closes the database connection."""
        self.conn.close()

# --- Self-contained Test Block ---
if __name__ == "__main__":
    import os
    import numpy as np
    from embedding import get_embedding
    from config import EMBEDDING_DIMENSION

    # Use a temporary, file-based database for a realistic and clean test
    TEST_DB_PATH = "test_memory.db"
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    print("--- Running DatabaseManager Test Suite ---")
    db = DatabaseManager(db_path=TEST_DB_PATH)
    
    try:
        # --- Test 1: Setup a multi-turn conversation with complex data ---
        print("\n1. Setting up a mock multi-turn conversation...")
        
        # Turn 1: A simple exchange
        turn_1_id = db.get_new_turn_id()
        db.add_message(turn_1_id, "user", "Hello! Please remember my favorite color is blue.")
        db.add_message(turn_1_id, "assistant", "Of course, I will remember that blue is your favorite color.")

        # Turn 2: A complex turn with thoughts and a tool call
        turn_2_id = db.get_new_turn_id()
        db.add_message(turn_2_id, "user", "What is the capital of France?")
        
        # This is the assistant's message, which includes thoughts and a tool call
        assistant_thoughts = "The user is asking a factual question. I should use a search tool."
        assistant_tool_calls = [{"function": {"name": "web_search", "arguments": {"query": "capital of France"}}}]
        db.add_message(
            turn_2_id, 
            "assistant", 
            "Let me check that for you.", 
            tool_calls=assistant_tool_calls, 
            thoughts=assistant_thoughts
        )
        print("  > Test data created successfully.")

        # --- Test 2: Verify get_long_term_history ---
        print("\n2. Testing get_long_term_history (for Turn 2)...")
        long_term_history = db.get_long_term_history(current_turn_id=turn_2_id)
        
        assert len(long_term_history) == 2, "Should ONLY retrieve the 2 messages from Turn 1."
        assert "blue" in long_term_history[0]['content'], "Should have the user message from Turn 1."
        assert "I will remember" in long_term_history[1]['content'], "Should have the assistant message from Turn 1."
        print("  > PASSED: Correctly retrieved only messages from previous turns.")

        # --- Test 3: Verify get_messages_for_turn ---
        print("\n3. Testing get_messages_for_turn (for Turn 2)...")
        turn_2_messages = db.get_messages_for_turn(turn_id=turn_2_id)

        assert len(turn_2_messages) == 2, "Should retrieve the 2 messages from Turn 2."
        
        # Inspect the complex assistant message
        user_message = turn_2_messages[0]
        assistant_message = turn_2_messages[1]
        
        assert user_message['role'] == 'user'
        assert assistant_message['role'] == 'assistant'
        
        # This is the most critical test:
        # Verify that the thoughts were correctly prepended to the content.
        assert assistant_message['content'].startswith(f"<think>{assistant_thoughts}</think>"), "Thoughts were not prepended correctly."
        assert "Let me check" in assistant_message['content'], "Original content is missing."
        
        # Verify that the tool_calls were correctly parsed.
        assert 'tool_calls' in assistant_message, "tool_calls key is missing."
        assert isinstance(assistant_message['tool_calls'], list), "tool_calls should be a list."
        assert assistant_message['tool_calls'][0]['function']['name'] == 'web_search', "Tool call was not parsed correctly."
        print("  > PASSED: Correctly reconstructed messages with thoughts and tool calls.")

        # --- Test 4: Verify get_long_term_history with debug print ---
        print("\n4. Testing get_long_term_history with more data (for Turn 3)...")
        turn_3_id = db.get_new_turn_id()
        db.add_message(turn_3_id, "user", "This is a new turn, and it should not appear in the long term history yet.")
        
        # Get history *before* this new turn
        long_term_history_for_turn_3 = db.get_long_term_history(current_turn_id=turn_3_id, limit=10)

        # The user-requested debug print statement
        print("--- DEBUG: get_long_term_history output ---")
        print(json.dumps(long_term_history_for_turn_3, indent=2))
        print("--- END DEBUG ---")

        # Verification: Should include all messages from Turn 1 (2) and Turn 2 (2)
        assert len(long_term_history_for_turn_3) == 4, "Should retrieve all 4 messages from Turns 1 and 2."
        
        # Verify content from Turn 1
        assert any("my favorite color is blue" in m.get('content', '') for m in long_term_history_for_turn_3)
        assert any("I will remember that blue" in m.get('content', '') for m in long_term_history_for_turn_3)
        
        # Verify content from Turn 2
        assert any("What is the capital of France?" in m.get('content', '') for m in long_term_history_for_turn_3)
        assert any("<think>" in m.get('content', '') and "Let me check that for you" in m.get('content', '') for m in long_term_history_for_turn_3)
        
        # Verify tool call from Turn 2 is present
        assistant_message_t2 = next((m for m in long_term_history_for_turn_3 if m['role'] == 'assistant' and 'tool_calls' in m), None)
        assert assistant_message_t2 is not None, "Assistant message with tool calls from Turn 2 should be in the history."
        assert assistant_message_t2['tool_calls'][0]['function']['name'] == 'web_search', "Tool call from Turn 2 was not found or is incorrect."
        
        print("  > PASSED: Correctly retrieved and verified the full history from previous turns.")

        # --- Test 5: Verify get_context_messages ---
        print("\n5. Testing get_context_messages with a word limit...")
        # The most recent message has 16 words.
        # The one before it has thoughts + content, totaling 19 words.
        # 16 + 19 = 35, so a limit of 30 should only return the most recent message.
        context_messages = db.get_context_messages(word_limit=30)

        print("--- DEBUG: get_context_messages output ---")
        print(json.dumps(context_messages, indent=2))
        print("--- END DEBUG ---")

        assert len(context_messages) == 1, "Should only retrieve the most recent message due to the word limit."
        assert "This is a new turn" in context_messages[0]['content'], "The content of the most recent message is incorrect."

        # Now, test with a larger limit to get more messages
        context_messages_larger = db.get_context_messages(word_limit=100)
        assert len(context_messages_larger) > 1, "Should retrieve more than one message with a larger word limit."
        print("  > PASSED: Correctly retrieved messages based on word limit.")

    finally:
        # --- Teardown: Ensure the test database is always cleaned up ---
        print("\n--- Cleaning up test database ---")
        db.close()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        print("--- All Tests Complete ---")
