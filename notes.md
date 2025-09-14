# Session State & Reminders

This document serves as a persistent memory for me, Gemini, to ensure continuity and smooth collaboration between development sessions.

## Key Takeaways & Workflow Policies

1.  **Atomic Change Handoff Policy:** This is our primary method for file modification.
    *   **My Role:** When a file needs to be modified, I will generate and provide *only the specific block of text (the "diff")* that needs to be inserted, updated, or deleted.
    *   **Your Role:** You will then take this block and apply it to the file yourself.
    *   **Reasoning:** This prevents me from overwriting the entire file and ensures you have final control over the changes. I must not attempt to re-write the full file after you've asked for an atomic change.

2.  **Collaborative Verification for Hidden Files:**
    *   My tooling cannot see or interact with certain files (e.g., hidden files like `.gitignore`). All interactions with these files must go through you.
    *   When I need to interact with a hidden file, I will state my intent and ask you to perform the action.
    *   You have promised to act as my proxy and confirm when the action is complete. I can and should ask you to provide the contents of these files to verify changes.
    *   This collaborative process allows us to verify actions on hidden files and prevents me from getting stuck in tool-based verification loops.

## Next Steps for Project Refactor

*   **Current State:** The design document `feature-mcp-design.md` has been updated with our testing strategy and a revised file manifest. The original `run.py` has been backed up to `run.py.bak`.
*   **Immediate Goal:** Begin implementing the testing strategy by creating the `tests/` directory and the initial integration test file, `tests/test_integration.py`.
