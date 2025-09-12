# Bashbot (Python Edition)

Bashbot is a command-line AI agent designed to interact with local models via the Ollama API. What started as an educational journey into Bash scripting has evolved into a robust, tool-using agent written in Python.

The core mission remains the same: to build a modular framework that allows powerful local language models to reason, act, and interact with their environment. This project is a testbed for creating agents that can solve problems, remember past interactions, and eventually achieve autonomous, multi-step task completion.

## Core Features

-   **Multiple Modes of Operation:**
    -   **One-Shot Mode:** Ask a single question and get a complete, tool-assisted answer. Perfect for scripting and quick queries.
    -   **Interactive Chat Mode:** A fast, stateful chat session for conversational Q&A.
    -   **Autonomous Agent Mode (Planned):** A future mode for long-running, complex tasks.
-   **Persistent, Two-Tiered Memory:**
    -   **Long-Term (RAG):** Bashbot saves conversations to a local SQLite database and uses a state-of-the-art RAG pipeline (with `nomic-embed-text`) to find and inject relevant, conceptually similar memories into its context.
    -   **Short-Term (Chronological):** The agent also recalls the most recent messages to maintain a natural conversational flow.
-   **Official Tool Use:** The agent uses the official Ollama `tools` API, allowing for reliable, structured interaction between the model and its capabilities.
-   **Modular Tools:** New tools can be added by creating a Python function and a corresponding JSON manifest, which are loaded automatically.
-   **Transparent Thinking:** See the agent's reasoning process and performance metrics (tokens/sec) streamed to your console in real-time.

## Getting Started

### Prerequisites

1.  **Ollama:** Must be installed and running. The setup script will attempt to install it for you if it's not found. See the [official Ollama site](https://ollama.com/).
2.  **Required Models:** The agent needs a primary reasoning model and an embedding model. The setup script will pull them for you.
    -   Reasoning Model: `gpt-oss:latest` (configurable in `.env`)
    -   Embedding Model: `nomic-embed-text:latest` (configurable in `.env`)
3.  **Python 3 & UV:** A working Python 3.10+ environment is required. This project uses `uv` for fast package management.
    ```shell
    # Install uv (if you don't have it)
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

### Installation

The setup process is fully automated.

1.  **Clone the repository:**
    ```shell
    git clone https://github.com/your-username/bashbot.git
    cd bashbot
    ```

2.  **Run the setup script:**
    This will install dependencies, pull the required models, and build the custom agent model.
    ```shell
    ./init.sh
    ```
    The script will also attempt to add a `bashbot` alias to your `~/.bashrc` file. You may need to restart your terminal or run `source ~/.bashrc` for it to take effect.

## Usage

Once the setup is complete, you can interact with the agent using the `run.sh` launcher or the `bashbot` alias.

**One-Shot Mode (with Tool Use):**
```shell
# Ask a question that requires memory
./run.sh "What did I say my favorite color was?"
# Or using the alias
bashbot "What is the latest news about NASA?"
```

**Interactive Chat Mode:**
```shell
./run.sh
> Hello, how are you?
> What is the capital of France?
> exit
```

## Project Roadmap

-   `[x]` **Phase 1: Foundational Architecture:** Professional Python environment, `.env` config, robust launcher.
-   `[x]` **Phase 2: Core Agent Logic:** One-Shot and Interactive modes, agentic loop, metrics.
-   `[x]` **Phase 3: Advanced Memory (RAG):** SQLite DB, automatic embedding, and a RAG-powered `memory_query` tool.
-   `[ ]` **Phase 4: Autonomous Agent Mode:** Implement the hierarchical task planner and manager.
-   `[ ]` **Phase 5: Expanded Toolset & Long-Term Wisdom:** Implement the "reflection" phase for the agent to learn from its completed tasks and populate a `lessons_learned` database.

## Acknowledgements

This project began as a personal quest to learn Bash scripting and evolved into a deep dive into AI agent architecture. The development was assisted and guided by conversation with Google's AI. It's a testament to the power of pairing human curiosity with AI collaboration.

The journey from a simple shell script to this Python-based agent has been a profound learning experience, and the goal is to continue pushing the boundaries of what a local, open-source agent can achieve.

