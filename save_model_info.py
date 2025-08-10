# file: bashbot_py/save_model_info.py

import requests
import json
import argparse
import sys

def fetch_and_save_model_info(model_name: str):
    """
    Fetches detailed information about a model from the Ollama API
    and saves it to a pretty-formatted text file.
    """
    ollama_host = "http://localhost:11434"
    api_endpoint = f"{ollama_host}/api/show"
    output_filename = f"model_info_{model_name.replace(':', '_')}.txt"

    print(f"Fetching information for model: '{model_name}'...")

    try:
        # --- 1. Make the API Call ---
        payload = {"model": model_name}
        response = requests.post(api_endpoint, json=payload)
        
        # Raise an exception for bad status codes (like 404 Not Found)
        response.raise_for_status()
        
        data = response.json()

        # --- 2. Parse and Format the Data ---
        # The 'modelfile', 'parameters', and 'template' fields are strings
        # with escaped newlines. We need to "un-escape" them.
        modelfile_content = data.get("modelfile", "N/A").replace("\\n", "\n").replace('\\"', '"')
        parameters_content = data.get("parameters", "N/A").replace("\\n", "\n")
        template_content = data.get("template", "N/A").replace("\\n", "\n").replace('\\"', '"')
        
        # The 'details' and 'model_info' fields are already objects,
        # so we can just pretty-print them.
        details_json = json.dumps(data.get("details", {}), indent=2)
        model_info_json = json.dumps(data.get("model_info", {}), indent=2)

        # --- 3. Write to the Output File ---
        with open(output_filename, 'w') as f:
            f.write(f"# Model Information for: {model_name}\n")
            f.write("=" * 40 + "\n\n")

            f.write("--- MODElFILE ---\n")
            f.write(modelfile_content)
            f.write("\n\n" + "=" * 40 + "\n\n")

            f.write("--- PARAMETERS ---\n")
            f.write(parameters_content)
            f.write("\n\n" + "=" * 40 + "\n\n")

            f.write("--- TEMPLATE ---\n")
            f.write(template_content)
            f.write("\n\n" + "=" * 40 + "\n\n")
            
            f.write("--- DETAILS ---\n")
            f.write(details_json)
            f.write("\n\n" + "=" * 40 + "\n\n")
            
            f.write("--- MODEL INFO ---\n")
            f.write(model_info_json)
            f.write("\n")

        print(f"Successfully saved model information to '{output_filename}'")

    except requests.exceptions.RequestException as e:
        print(f"\nAPI Error: Could not connect to Ollama at {ollama_host}. Is the server running?", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"\nError: Model '{model_name}' not found by Ollama.", file=sys.stderr)
        else:
            print(f"\nHTTP Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and pretty-save information about an Ollama model."
    )
    parser.add_argument(
        "model_name", 
        type=str, 
        help="The name of the model to show (e.g., 'bashbot' or 'llama3:8b')."
    )
    args = parser.parse_args()
    
    fetch_and_save_model_info(args.model_name)
