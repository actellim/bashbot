from database import DatabaseManager
from config import SEARXNG_HOST, SEARCH_RESULTS_TO_SHOW

import requests
from urllib.parse import quote
from bs4 import BeautifulSoup


#---Tool Functions---
def memory_query(db: DatabaseManager, query: str) -> str:
    """
    Searches the conversation memroy for a specific keyword or phrase.
    This is the actual Python function that gets executed when the 'memory_query' tool is called.
    """
    # print(f"[DEBUG_TOOL] Executing memory_query with query: '{query}'")
    if not query:
        return "[TOOL_ERROR] No search term provided."

    try:
        # The search_memory function in our database manager does allllll the heavy lifting.
        results = db.search_memory(search_term=query)
        return results
    except Exception as e:
        return f"[TOOL_ERROR] An error occurred while searching memory: {e}"

def web_search(query: str) -> str:
    """
    Performs a web search using the local SearXNG instance and returns a summary.
    """
    # print(f"[DEBUG_TOOL] Executing web_search with query: '{query}'")
    if not query:
        return "[TOOL_ERROR] No search term provided."

    try:
        # URL-encode the query to handle spaces and special characters
        safe_query = quote(query)
        search_url = f"{SEARXNG_HOST}/search?q={safe_query}&format=json"

        response = requests.get(search_url, timeout=10)
        response.raise_for_status()

        search_results = response.json()

        #---Summarize---
        # Avoid overfilling the context window with raw json.
        output = f"---Web Search Results for '{query}'---\n\n"
        results_to_show = search_results.get("results", [])[:SEARCH_RESULTS_TO_SHOW]

        if not results_to_show:
            return f"No results found for '{query}'."

        for i, result in enumerate(results_to_show, 1):
            output += f"Result {i}:\n"
            output += f"    Title: {result.get('title', 'N/A')}\n"
            output += f"    URL: {result.get('url', 'N/A')}\n"
            output += f"    Content: {result.get('content', 'N/A')}\n\n"
        return output

    except requests.exceptions.RequestException as e:
        return f"[TOOL_ERROR] Could not connect to the search service: {e}"
    except Exception as e:
        return f"[TOOL_ERROR] An error occurred during the web search: {e}"

'''
def web_reader(url: str) -> str:
    """ 
    Fetches the clean, readable text from a URL. 
    This is a simplified version; real-world scraping can be much more complex. 
    """ 
    print(f"[DEBUG_TOOL] Executing web_reader with URL: '{url}'")
    if not url:
        return "[TOOL_ERROR] No URL provided."

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # BeautifulSoup parses the HGML and extracts text
        soup = BeautifulSoup(response.text, 'html.parser')

        # This is a simple approach, it gets ALL text.
        # More advanced parsing looks for the main tags: <article>, <main>, etc.
        clean_text = soup.get_text(separator='\n', strip=True)

        # Turncate the content to avoid overflowing the context window.
        # Should make this configurable later.
        return clean_text[:4000]

    except requests.exceptions.RequestException as e:
        return f"[TOOL_ERROR] Could not fetch URL {url}. Error: {e}" 
    except Exception as e:
        return f"[TOOL_ERROR] An error occurred while reading the URL: {e}"
'''
#---Tool Dispatcher---
# This dictionary maps the tool name (from the JSON manifest)
# to the actual python function to be called. This is a clean and
# scalable way to manage your tools.
AVAILABLE_TOOLS = {
        # When you add a new tool, like 'web_search', you will:
        # 1. Write the function: def web_search(query: str) -> str: ...
        # 2. Add it to THIS dictionary: "web_search": web_search,
        "memory_query": memory_query,
        "web_search": web_search,
        # "web_reader": web_reader,
        }


