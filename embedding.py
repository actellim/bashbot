import requests
import json
import sys

try:
    from config import OLLAMA_HOST, EMBEDDING_MODEL
except ImportError:
    OLLAMA_HOST = "http://localhost:11434"
    EMBEDDING_MODEL = "nomic-embed-text:latest"

def get_embedding(text:str) -> list[float]:
    """
    Generates an embedding vector for a given piece of text using the Ollama API.
    """
    try:
        payload = {
                "model": EMBEDDING_MODEL,
                "prompt": text
                }
        response = requests.post(f"{OLLAMA_HOST}/api/embeddings", json=payload)
        response.raise_for_status()

        return response.json().get("embedding", [])

    except requests.exceptions.RequestException as e:
        print(f"API Error: Could not get embedding. Is Ollama running? Details: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An unexpected error occurred in get_embedding: {e}", file=sys.stderr)
        return []

#---Test---
if __name__ == "__main__":
    print(f"---Running embedding Test---")
    print(f"Using embedding model: {EMBEDDING_MODEL}")

    test_text_1 = "Hello, world!"
    test_text_2 = "Hola, mundo!"

    print(f"\nGenerating embedding for: '{test_text_1}'")
    embedding_1 = get_embedding(test_text_1)

    if embedding_1:
        print(f"    > Success! Got a vector of {len(embedding_1)} dimensions.")
        print(f"    > First 5 dimensions: {embedding_1[:5]}")
        assert len(embedding_1) > 0, "Embedding should not be emtpy"
    else:
        print("     > FAILED to get embedding.")
        sys.exit(1)

    print(f"\nGenerating embedding for: '{test_text_2}'")
    embedding_2 = get_embedding(test_text_2)

    if embedding_2:
        print(f"    > Success! Got a vector of {len(embedding_2)} dimensions.")
        print(f"    > First 5 dimensions: {embedding_2[:5]}")
        assert len(embedding_2) > 0, "Embedding should not be emtpy"
    else:
        print("     > FAILED to get embedding.")
        sys.exit(1)

    print("\n---Test Complete---")
