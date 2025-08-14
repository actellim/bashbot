import os
from dotenv import load_dotenv

load_dotenv()

#---Ollama Config---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "bashbot")
BASE_MODEL = os.getenv("BASE_MODEL", "gpt-oss:latest")
MODEL_CONTEXT_WINDOW = int(os.getenv("MODEL_CONTEXT_WINDOW", 24000))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 768))
VECTOR_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", 1.0))

#---Agent Config---
CONTEXT_WORD_LIMIT = int(os.getenv("CONTEXT_WORD_LIMIT", 1800))
MAX_AGENT_TURNS = int(os.getenv("MAX_AGENT_TURNS", 5))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

#---Path Config---
DB_PATH = os.getenv("DB_PATH", "memory.db")
TOOLS_DIR = os.getenv("TOOLS_DIR", "tools")

#---Search Config---
SEARXNG_HOST = "http://localhost:8080"
SEARCH_RESULTS_TO_SHOW = 5

#---Print Colors---
class Colors:
    GREY = '\033[90m'
    RESET = '\033[0m'
