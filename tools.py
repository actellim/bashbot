from database import DatabaseManager

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


#---Tool Dispatcher---
# This dictionary maps the tool name (from the JSON manifest)
# to the actual python function to be called. This is a clean and
# scalable way to manage your tools.
AVAILABLE_TOOLS = {
        "memory_query": memory_query,
        # When you add a new tool, like 'web_search', you will:
        # 1. Write the function: def web_search(query: str) -> str: ...
        # 2. Add it to THIS dictionary: "web_search": web_search,
        }

