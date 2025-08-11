import json
import os
import argparse
import requests
import sys

from database import DatabaseManager
from config import *
from tools import AVAILABLE_TOOLS

def load_tool_manifests(tools_dir: str) -> list:
    """Loads all tool manifest .json files from the specified directory."""
    manifests = []
    if not os.path.isdir(tools_dir):
        print(f"Warning: Tools directory not found at '{tools_dir}'", file=sys.stderr)
        return manifests

    for filename in os.listdir(tools_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(tools_dir, filename)
            with open(filepath, 'r') as f:
                manifest = json.load(f)
                manifests.append(manifest)
    return manifests

def main():
    #---1: Setup---
    parser = argparse.ArgumentParser(description="A command-line AI agent that uses tools.")
    parser.add_argument("prompt", type=str, help="The initial prompt for the agent.")
    args = parser.parse_args()

    db = DatabaseManager(DB_PATH)
    tools_manifests = load_tool_manifests(TOOLS_DIR)

    turn_id = db.get_new_turn_id()

    # This list will hold the messages for the current turn as the conversatio nevolves.
    messages_for_turn = [{"role": "user", "content": args.prompt}]

    #---2: The Agentic Loop---
    for i in range(MAX_AGENT_TURNS):
        #---3: API Call---
        history = db.get_context_messages(CONTEXT_WORD_LIMIT)
        if i == 0:
            db.add_message(turn_id, "user", args.prompt)
        full_message_history = history + messages_for_turn

        payload = {
                "model": MODEL_NAME,
                "messages": full_message_history,
                "tools": tools_manifests,
                "stream": True,
                "think": True
                }

        #---4: Process---
        full_content = ""
        full_thoughts = ""
        tool_calls = []
        thinking_printed = False
        response_printed = False

        try:
            with requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True) as response:
                response.raise_for_status() # Will raise an exception for bad status codes
                for chunk in response.iter_lines():
                    if chunk:
                        chunk_json = json.loads(chunk)

                        thinking_part = chunk_json['message'].get('thinking', '')
                        if thinking_part:
                            if not thinking_printed:
                                print(f"{Colors.GREY}Thinking:{Colors.RESET}", end='', flush=True)
                                thinking_printed = True
                            print(f"{Colors.GREY}{thinking_part}{Colors.RESET}", end='', flush=True) 
                            full_thoughts += thinking_part

                        content_part = chunk_json['message'].get('content', '')
                        if content_part:
                            if not response_printed:
                                print(f"\nResponse: ", end='', flush=True)
                                response_printed = True
                            print(content_part, end='', flush=True)
                            full_content += content_part

                        if chunk_json['message'].get('tool_calls'):
                            tool_calls.extend(chunk_json['message']['tool_calls'])

                        if chunk_json.get('done'):
                            break

        except requests.exceptions.RequestException as e:
            print(f"\nAPI Error: Could not connect to Ollama. Is the server running? Details: {e}", file=sys.stderr)
            db.close()
            return

        print() # Final newline after streaming is done.

        #---5: Save and Decide---
        # Save the assistant's complete message (which might be thoughts and a final answer)
        db.add_message(turn_id, "assistant", full_content, tool_calls, thoughts=full_thoughts)

        if not tool_calls:
            print(f"\n{Colors.GREY}---Task Complete---{Colors.RESET}")
            break

        messages_for_turn.append({"role": "assistant", "content": full_content, "tool_calls": tool_calls})

        for tool_call in tool_calls:
            tool_name = tool_call['function']['name']
            tool_args = tool_call['function']['arguments']

            print(f"{Colors.GREY}<Executing tool: {tool_name}({json.dumps(tool_args)})>{Colors.RESET}")

            if tool_name in AVAILABLE_TOOLS:
                tool_function = AVAILABLE_TOOLS[tool_name]

                import inspect
                func_sig = inspect.signature(tool_function)
                final_tool_args = tool_args
                if 'db' in func_sig.parameters:
                    final_tool_args['db'] = db

                try:
                    # Execute the tool function, passing the DB and args
                    result_content = str(tool_function(**final_tool_args))
                except Exception as e:
                    result_content = f"[TOOL_ERROR] An unexpected error occurred: {e}"

                # Add the tool's result to the message history for the next loop 
                tool_response_message = {"role": "tool", "content": result_content}
                messages_for_turn.append(tool_response_message)
                db.add_message(turn_id, "tool", result_content)
            else:
                print(f"{Colors.GREY}[TOOL_ERROR] Model tried to call unknown tool: {tool_name}{Colors.RESET}")
                error_message = f"Tool '{tool_name}' not found in available tools."
                messages_for_turn.append({"role": "tool", "content": error_message})
                db.add_message(turn_id, "tool", error_message)

    db.close()

if __name__ == "__main__":
    main()

