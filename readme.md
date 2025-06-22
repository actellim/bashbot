# Bashbot

Bashbot is a command line tool designed to invoke a model in ollama through the shell. 

## Future Plans

- Implement a way to store calls.
- Implement a way to search through past calls as a form of psuedo "memory".
- Design tools for the model to use, specifically:
    - A way for the model to query it's own memories.
    - A way for the model to conduct internet searches.
    - A scratchpad for the model to send messages to it's future self once the context has been exhausted.
    - A tool editor to allow the model to design and edit it's own tools.
- A way to run the model on loop until a task is completed.

## To Do

- [x] Create a `db_setup.sh` script that creates the `memory.db` file and the main table.
- [x] Create the `conversations` table schmea.
- [x] Create a library of helper functions `lib/database.sh` that can be sourced from `bashbot.sh`.
- [x] Write bashbot.sh v0.2
    - [x] Get the prompt from the user and store it in `memory.db`.
    - [x] Send the last `N` messages from the `.db` to form the conversation context. (*The n_context is probably important for determining this.*)
    - [x] Send the prompt and the conversation context to ollama.
    - [x] Stream the model's response. (*Have an option to leave the stream on or wait for a response without a tool call?*)
- [ ] Create a `tools/` directory and build tools for:
    - [ ] `scratchpad`
    - [ ] `memory_query`
- [ ] Write bashbot.sh v0.3
    - [ ] Parse the response to look for a tool call. (*Refer to the ollama docs for formatting best practices with the tool api*)
    - [ ] Loop if tool tag found, else finish the conversation.
- [ ] Build tool for:
    - [ ] `search`
- [ ] Setup a sandbox for the model to execute code
- [ ] Build the `tool_editor` tool.
- [ ] Build tests for the `tool_editor` before new tools are added to the toolbox.
- [ ] Build a test procedure to measure effectiveness of new tools and decide to progress/rollback the toolbox.

## Acknowledgements

[Script development and debugging assisted by Google's AI](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221aqqK6jebLWdy1fp3_kA5al-kBr9Rzbmw%22%5D,%22action%22:%22open%22,%22userId%22:%22113617653760645723737%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing)
