import sqlite3

DB_PATH = "memory.db"

def setup_database():
    """Creates all necessary tables for the agent's memory and planning."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("---Setting up DB schema---")

    #---Core Converstaion Memory---
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS conversations(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       task_id INTEGER,
                       turn_id INTEGER NOT NULL,
                       timestamp TEXT NOT NULL,
                       role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),
                       content TEXT NOT NULL,
                       tool_calls TEXT,
                       thoughts TEXT,
                       embedding BLOB,
                       FOREIGN KEY (task_id) REFERENCES tasks(id)
                       );
                   """)
    print("Table 'conversations' created or already exists.")

    #---Agent's Task Planner---
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tasks (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       parent_id INTEGER,
                       description TEXT NOT NULL,
                       status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')),
                       created_at TEXT NOT NULL,
                       completed_at TEXT,
                       FOREIGN KEY(parent_id) REFERENCES tasks(id)
                       );
                   """)
    print("Table 'tasks' created or already exists.")

    #---Summarized Memories---
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS summaries (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       task_id INTEGER,
                       source_conversation_ids TEXT NOT NULL,
                       summary_content TEXT NOT NULL,
                       created_at TEXT NOT NULL,
                       embedding BLOB,
                       FOREIGN KEY (task_id) REFERENCES tasks(id)
                       );
                   """)
    print("Table 'summaries' created or already exists.")

    #---Agent's Long-Term Wisdom---
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS lessons_learned (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       related_task_id INTEGER,
                       lesson TEXT NOT NULL,
                       created_at TEXT NOT NULL,
                       embedding BLOB,
                       FOREIGN KEY (related_task_id) REFERENCES tasks(id)
                       );
                   """)
    print("Table 'lessons_learned' created or already exists.")

    conn.commit()
    conn.close()
    print("---Database setup complete!---")

if __name__ == "__main__":
    setup_database()

