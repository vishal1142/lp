#!/bin/bash

# Change this if you want a custom commit message
DEFAULT_COMMIT_MSG="SHELL SCRIPTING Auto-commit on $(date '+%Y-%m-%d %H:%M:%S')"

# Ask for a custom commit message (optional)
read -p "Enter commit message (or press Enter for default): " COMMIT_MSG

# If no input, use default
if [ -z "$COMMIT_MSG" ]; then
  COMMIT_MSG="$DEFAULT_COMMIT_MSG"
fi

# Run Git commands
git add .
git commit -m "$COMMIT_MSG"
git push origin main

echo "✅ Code pushed to GitHub!"
echo "Commit message: $COMMIT_MSG"
echo "Branch: main"
echo "Repository: $(git remote get-url origin)"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "----------------------------------------"
echo "Push completed successfully!"
echo "----------------------------------------"
echo "You can now check your GitHub repository for the latest changes."
echo "----------------------------------------"
echo "Thank you for using the auto-push script!"
echo "----------------------------------------"
echo "If you have any questions or feedback, feel free to reach out."
echo "----------------------------------------"
echo "Have a great day!"
# echo sh auto-push.sh
# echo sh auto-push.sh
# echo sh auto-push.sh
