# Bashbot (Now in Python!)

Bashbot is a command-line AI agent designed to interact with local models via the Ollama API. What started as an educational journey into the world of Bash scripting has evolved into a robust, tool-using agent written in Python.

The core mission remains the same: to build a modular framework that allows powerful local language models to reason, act, and interact with their environment. This project is a testbed for creating autonomous agents that can solve problems, remember past interactions, and learn to use new tools.

## Core Features

- **Persistent Memory:** Bashbot saves every conversation to a local SQLite database, allowing it to recall past interactions and build context over time.
- **Agentic Loop (ReAct Framework):** The agent can reason about a user's prompt, decide to use a tool, execute it, and use the results to formulate a final answer.
- **Dynamic Tool Use:** The agent uses the official Ollama `tools` API. New tools can be added by simply creating a Python function and a corresponding JSON manifest, which are loaded automatically at runtime.
- **Streaming Responses:** Get real-time feedback from the model, including its "thinking" process, which is printed to the console for transparency.

## Getting Started

### Prerequisites

1.  **Ollama:** You must have Ollama installed and running. See the [official Ollama site](https://ollama.com/) for installation instructions.
2.  **A Tool-Using Model:** This agent is designed for a model that supports the Ollama tools API. The current development model is `gpt-oss`.
3.  **Python 3:** You will need Python 3 and the `requests` library.
    ```shell
    pip install requests
    ```

### Installation

1.  **Clone the repository:**
    ```shell
    git clone https://github.com/your-username/bashbot.git
    cd bashbot
    ```

2.  **Build the Custom Model:**
    The agent uses a custom model with a specific template and system prompt. Run the build script to create it.
    ```shell
    ./build_model.sh
    ```
    This will create a new model in Ollama named `bashbot` based on the configuration in the `Modelfile`.

3.  **Run the Agent:**
    You can now run the agent from your command line.
    ```shell
    python3 agent.py "What is my favorite color?"
    ```

## Project Roadmap & Future Plans

This project is a continuous exploration of agentic AI. Here's where we're headed:

-   **[x] Persistent Memory:** Implement a robust SQLite database for conversation history.
-   **[x] Tool Use Foundation:** Build a modular system for defining and executing tools.
-   **[x] First Tool: `memory_query`:** Create a tool that allows the agent to search its own memory.
-   **[ ] Second Tool: Internet Search:** Implement a tool that allows the agent to search the web to answer questions about current events.
-   **[ ] Third Tool: Scratchpad:** A tool for long-term, condensed memory, allowing the agent to save key insights for its future self.
-   **[ ] Advanced Agency: The `tool_editor`:** The ultimate goal. A tool that allows the model to write and modify its *own* tools, enabling true self-improvement.
    -   This will require a secure, sandboxed environment for code execution.
-   **[ ] Autonomous Operation:** Develop a "main loop" that allows the agent to run continuously on a task, breaking it down into sub-problems and using tools until the goal is complete.

## Acknowledgements & Notes

This project began as a personal quest to better understand Bash scripting and the fundamentals of how shells work, with invaluable educational assistance from Google's AI. The journey from a simple shell script to this Python-based agent has been a profound learning experience.

For anyone learning to code, I highly recommend this approach: pick a project that fascinates you, be persistent, and don't be afraid to ask for help—whether from an AI tutor or a human one. The process of debugging, failing, and finally succeeding is where the real learning happens.
