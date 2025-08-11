# file: bashbot_py/run_tool.py
# A more robust script to manually test any single-argument tool.

import argparse
import json
import os
from database import DatabaseManager
from tools import AVAILABLE_TOOLS
from config import DB_PATH, TOOLS_DIR

def main():
    parser = argparse.ArgumentParser(description="Manually run an agent tool.")
    parser.add_argument("tool_name", type=str, choices=AVAILABLE_TOOLS.keys(), help="The name of the tool to run.")
    parser.add_argument("argument", type=str, help="The string argument to pass to the tool (e.g., a search query or a URL).")
    args = parser.parse_args()

    # --- Setup ---
    db = DatabaseManager(DB_PATH)
    tool_function = AVAILABLE_TOOLS.get(args.tool_name)

    # --- Dynamically find the tool's argument name from its manifest ---
    argument_name = None
    try:
        manifest_path = os.path.join(TOOLS_DIR, f"{args.tool_name}.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            # Find the first (and only) required parameter name
            argument_name = manifest['function']['parameters']['required'][0]
    except (FileNotFoundError, IndexError, KeyError):
        print(f"Error: Could not determine the argument name for '{args.tool_name}' from its manifest.")
        return

    print(f"--- Running tool '{args.tool_name}' with {argument_name}='{args.argument}' ---")

    # Build the arguments dictionary dynamically
    tool_arguments = {argument_name: args.argument}
    
    # Prepare the final arguments for the function call
    final_args = {}
    if args.tool_name == "memory_query":
        final_args['db'] = db
    
    # Add the dynamically found arguments
    final_args.update(tool_arguments)

    try:
        result = tool_function(**final_args)
        print("\n--- Tool Result ---")
        print(result)
    except Exception as e:
        print(f"\n--- Tool Error ---")
        print(f"An error occurred: {e}")
        
    db.close()

if __name__ == "__main__":
    main()
