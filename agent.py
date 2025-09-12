from database import DatabaseManager


class Agent:
    """A class that handles the agents executive function: traffic control, memory, and actions."""

    def __init__(self, db = DatabaseManager, tool_manifests= list):
        """
        Initializes the class and its dependencies.

        Args:
            db: An active DatabaseManager instance.
            tool_manifests: A list of tool manifest dictionaries.
        """
        self.db = db
        self.tool_manifests = tool_manifests
        print("[AGENT_INIT] Agent initialized with database connection and tool manifests.")

    
