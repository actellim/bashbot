import json
import os
import argparse
import requests
import sys
import numpy as np

from embedding import get_embedding
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
                manifests.append(json.load(f))
    return manifests

def run_agentic_turn(initial_prompt: str, db: DatabaseManager, tool_manifests: list):
    """
    Runs the full agentic loop for a single user request.
    This includes reasoning, tool calls, and generating a final response.
    """

    turn_id = db.get_new_turn_id()
    db.add_message(turn_id, "user", initial_prompt)
    history = db.get_long_term_history(current_turn_id=turn_id)
    final_stats_chunk = {}

    #---2: The Agentic Loop---
    for i in range(MAX_AGENT_TURNS):

        #---3: API Call---
        messages_for_this_turn = db.get_messages_for_turn(turn_id=turn_id)
        # Get relevent associateve memories using most recent message as query source.
        rag_query_text = messages_for_this_turn[-1]['content']
        print(f"{Colors.GREY}[CONTEXT] Searching for memories related to: '{rag_query_text[:50]}...'{Colors.RESET}")

        query_vector = get_embedding(rag_query_text)
        important_memories = []
        if query_vector:
            query_np_vector = np.array(query_vector, dtype=np.float32)
            similar_memories = db.find_similar_memories(query_np_vector, top_k=5)

            turn_content = {msg['content'] for msg in messages_for_this_turn}
            history_content = {msg['content'] for msg in history}
            content_to_ignore = turn_content | history_content
            relevant_memories = [mem for mem in similar_memories if mem['content'] not in content_to_ignore]

            if relevant_memories:
                rag_context_content = "---Relevant Long-Term Memories---\n"
                for mem in relevant_memories:
                    rag_context_content += f"Memory from Turn {mem['turn_id']} ({mem['role']}): {mem['content']}\n"
                # Add the RAG context as the first system message.
                important_memories = [{"role": "system", "content": rag_context_content.strip()}]

        # Assemble the full message history for the API call
        full_message_history = important_memories + history + messages_for_this_turn
        print(f"The message being sent to the bot now is {full_message_history}.")

        payload = {
                "model": MODEL_NAME,
                "messages": full_message_history,
                "tools": tool_manifests,
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
                                print(f"{Colors.GREY}Thinking:{Colors.RESET} ", end='', flush=True)
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
                            final_stats_chunk = chunk_json
                            break

        except requests.exceptions.RequestException as e:
            print(f"\nAPI Error: Could not connect to Ollama. Is the server running? Details: {e}", file=sys.stderr)
            return

        print() # Final newline after streaming is done.

        #---5: Save and Decide---
        # Save the assistant's complete message (which might be thoughts and a final answer)
        db.add_message(turn_id, "assistant", full_content, tool_calls, thoughts=full_thoughts)

        if not tool_calls:
            # IT'S A FINAL ANSWER
            print(f"\n{Colors.GREY}---Task Complete---{Colors.RESET}")
            break

        for tool_call in tool_calls:
            tool_name = tool_call['function']['name']
            tool_args = tool_call['function']['arguments']

            print(f"\n{Colors.GREY}<Executing tool: {tool_name}({json.dumps(tool_args)})>{Colors.RESET}")

            if tool_name in AVAILABLE_TOOLS:
                tool_function = AVAILABLE_TOOLS[tool_name]
                try:
                    import inspect
                    func_sig = inspect.signature(tool_function)
                    final_tool_args = tool_args
                    if 'db' in func_sig.parameters:
                        final_tool_args['db'] = db

                    result_content = str(tool_function(**final_tool_args))
                except Exception as e:
                    result_content = f"[TOOL_ERROR] An unexpected error occurred: {e}"

                db.add_message(turn_id, "tool", result_content)
                print(f"{Colors.GREY}<Tool Output>\n{result_content}\n</Tool Output>{Colors.RESET}")
            else:
                error_message = f"Tool '{tool_name}' not found."
                print(f"{Colors.GREY}[TOOL_ERROR] {error_message}{Colors.RESET}")
                db.add_message(turn_id, "tool", error_message)
            
    #---6: Print Metrics---
    # This block now runs after the agentic loop (for i in range...) is finished.
    if final_stats_chunk:
        prompt_tokens = final_stats_chunk.get('prompt_eval_count', 0)
        response_tokens = final_stats_chunk.get('eval_count', 0)

        eval_duration_ns = final_stats_chunk.get('eval_duration', 1)
        # Prevent division by zero if duration is 0
        tokens_per_sec = response_tokens / (eval_duration_ns / 1_000_000_000) if eval_duration_ns > 0 else 0

        total_context = MODEL_CONTEXT_WINDOW

        print(f"\n{Colors.GREY}---Metrics---")
        print(f"Context: {prompt_tokens} / {total_context} tokens")
        print(f"Output: {response_tokens} tokens")
        print(f"Speed: {tokens_per_sec:.2f} tokens/sec")
        print(f"-------------{Colors.RESET}")

def run_interactive_mode(db: DatabaseManager, tool_manifests: list):
    """Starts a continuous chat session that uses the full agentic loop."""
    print("--- Bashbot Interactive Mode ---")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ["exit", "quit"]:
                break
            if not prompt: # Handle empty input
                continue
            
            # For each line of input, we simply call our main agentic function.
            # It will handle its own database saving, context retrieval, and tool use.
            run_agentic_turn(prompt, db, tool_manifests)

        except KeyboardInterrupt:
            # Allows for a clean exit with Ctrl+C
            print("\nExiting...")
            break

def main():
    """Main entry point, parses arguments and routes to the correct mode."""
    parser = argparse.ArgumentParser(description="A command-line AI agent that uses tools.")
    parser.add_argument("prompt", nargs='?', default=None, help="The initial prompt for the agent in one-shot mode.")
    parser.add_argument("--agent", type=str, dest='agent_goal', help="Run in autonomous agent mode with the given high-level goal.")
    args = parser.parse_args()

    db = DatabaseManager(DB_PATH)
    tool_manifests = load_tool_manifests(TOOLS_DIR)

    if args.agent_goal:
        print(f"---Autonomous Agent Mode---")
        print(f"Goal: {args.agent_goal}")
        print("Note: Autonomous mode is not yet implemented")
        # Future: call run_autonomous_mode(args.agent_goal, db, tool_manifests)
    elif args.prompt:
        #---One-Shot---
        run_agentic_turn(args.prompt, db, tool_manifests)
    else:
        #---Interactive---
        run_interactive_mode(db, tool_manifests)

    db.close()

if __name__ == "__main__":
    main()

