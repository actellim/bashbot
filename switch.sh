#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- CONFIGURATION ---
DB_NAME="memory.db"
REQUIREMENTS_FILE="requirements.txt"
# ---------------------

# 1. Check if a target branch was provided
if [ -z "$1" ]; then
  echo "Usage: ./switch.sh <branch-name>"
  exit 1
fi

TARGET_BRANCH=$1
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Replaces all occurrences of '/' with '-'
SANITIZED_CURRENT_BRANCH=${CURRENT_BRANCH//\//-}
SANITIZED_TARGET_BRANCH=${TARGET_BRANCH//\//-}
# ----------------------------------------------------

echo "Current branch is '$CURRENT_BRANCH'"

if [ "$CURRENT_BRANCH" == "$TARGET_BRANCH" ]; then
  echo "Already on branch '$TARGET_BRANCH'. Ensuring environment is synced with uv."
  uv pip sync "$REQUIREMENTS_FILE"
  echo "Done."
  exit 0
fi

# 3. Save the database for the current branch (using sanitized name)
if [ -f "$DB_NAME" ]; then
  echo "Saving database for branch '$CURRENT_BRANCH' to '$DB_NAME.$SANITIZED_CURRENT_BRANCH'"
  mv "$DB_NAME" "$DB_NAME.$SANITIZED_CURRENT_BRANCH" # <-- USE SANITIZED
else
  echo "No database file ('$DB_NAME') found to save."
fi

# 4. Switch to the new branch
echo "Switching to branch '$TARGET_BRANCH'..."
git checkout "$TARGET_BRANCH"

# 5. Restore the database for the new branch (using sanitized name)
if [ -f "$DB_NAME.$SANITIZED_TARGET_BRANCH" ]; then # <-- USE SANITIZED
  echo "Restoring database for branch '$TARGET_BRANCH' from '$DB_NAME.$SANITIZED_TARGET_BRANCH'"
  mv "$DB_NAME.$SANITIZED_TARGET_BRANCH" "$DB_NAME" # <-- USE SANITIZED
else
  echo "No saved database found for branch '$TARGET_BRANCH'. You may need to create one."
fi

# 6. Sync the Python virtual environment with uv
echo "Syncing Python environment with uv from '$REQUIREMENTS_FILE'..."
if [ -f "$REQUIREMENTS_FILE" ]; then
  uv pip sync "$REQUIREMENTS_FILE"
else
    echo "Warning: No '$REQUIREMENTS_FILE' found on this branch."
fi

echo "Successfully switched to branch '$TARGET_BRANCH'."
