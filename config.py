import os
from dotenv import load_dotenv

#---Path Config:
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

#---Ollama Config---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "bashbot")
BASE_MODEL = os.getenv("BASE_MODEL", "gpt-oss:latest")
MODEL_CONTEXT_WINDOW = int(os.getenv("MODEL_CONTEXT_WINDOW", 24000))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 768))
VECTOR_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", 30.0))

#---Agent Config---
CONTEXT_WORD_LIMIT = int(os.getenv("CONTEXT_WORD_LIMIT", 1800))
MAX_AGENT_TURNS = int(os.getenv("MAX_AGENT_TURNS", 5))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

#---Path Config---
DB_PATH = os.path.join(PROJECT_ROOT, os.getenv("DB_PATH", "memory.db"))
TOOLS_DIR = os.path.join(PROJECT_ROOT, os.getenv("TOOLS_DIR", "tools"))

#---Search Config---
SEARXNG_HOST = "http://localhost:8080"
SEARCH_RESULTS_TO_SHOW = 5

#---Print Colors---
class Colors:
    GREY = '\033[90m'
    RESET = '\033[0m'

# --- Self-contained Test Block ---
# This code only runs if you execute `python3 config.py` directly.
if __name__ == "__main__":
    import os

    print("--- Running config.py Test & Verification ---")

    # --- 1. Display Loaded Values ---
    print("\n--- Loaded Values from .env (or defaults) ---")
    print(f"  OLLAMA_HOST: {OLLAMA_HOST}")
    print(f"  MODEL_NAME: {MODEL_NAME}")
    print(f"  BASE_MODEL: {BASE_MODEL}")
    print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    print(f"  MODEL_CONTEXT_WINDOW: {MODEL_CONTEXT_WINDOW}")
    print(f"  CONTEXT_WORD_LIMIT: {CONTEXT_WORD_LIMIT}")
    print(f"  MAX_AGENT_TURNS: {MAX_AGENT_TURNS}")
    print(f"  VECTOR_SIMILARITY_THRESHOLD: {VECTOR_SIMILARITY_THRESHOLD}")

    # --- 2. Type Verification ---
    print("\n--- Verifying Data Types ---")
    try:
        assert isinstance(MODEL_CONTEXT_WINDOW, int)
        print("  > MODEL_CONTEXT_WINDOW is correctly an integer.")
        assert isinstance(CONTEXT_WORD_LIMIT, int)
        print("  > CONTEXT_WORD_LIMIT is correctly an integer.")
        assert isinstance(EMBEDDING_DIMENSION, int)
        print("  > EMBEDDING_DIMENSION is correctly an integer.")
        assert isinstance(VECTOR_SIMILARITY_THRESHOLD, float)
        print("  > VECTOR_SIMILARITY_THRESHOLD is correctly a float.")
        print("  > All type checks PASSED.")
    except AssertionError as e:
        print(f"  > Type check FAILED: {e}")

    # --- 3. Path Verification ---
    print("\n--- Verifying Constructed Paths ---")
    print(f"  > Project Root: {PROJECT_ROOT}")
    print(f"  > Database Path: {DB_PATH}")
    print(f"  > Tools Dir Path: {TOOLS_DIR}")
    try:
        assert os.path.isabs(DB_PATH), "DB_PATH should be an absolute path."
        assert os.path.isabs(TOOLS_DIR), "TOOLS_DIR should be an absolute path."
        assert os.path.isdir(TOOLS_DIR), "The TOOLS_DIR path does not point to an existing directory."
        print("  > All path checks PASSED.")
    except AssertionError as e:
        print(f"  > Path check FAILED: {e}")

    print("\n--- Configuration tests complete ---")
