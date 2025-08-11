# file: capture_final_chunk.py
import requests
import json
from config import MODEL_NAME, OLLAMA_HOST

# A simple prompt that will generate a short response
payload = {
    "model": MODEL_NAME,
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": True
}

print(f"--- Capturing stream from model '{MODEL_NAME}' to find final 'done' object ---")

raw_chunks = []
with requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True) as response:
    for chunk in response.iter_lines():
        if chunk:
            raw_chunks.append(chunk.decode('utf-8')) # Save the raw string

# The last line is the one we care about
final_line = raw_chunks[-1] if raw_chunks else "{}"

print("\n--- Raw Final JSON Chunk ---")
print(final_line)

print("\n--- Pretty-Printed Final JSON Chunk ---")
try:
    final_json = json.loads(final_line)
    print(json.dumps(final_json, indent=2))
except json.JSONDecodeError as e:
    print(f"Error parsing final chunk as JSON: {e}")
