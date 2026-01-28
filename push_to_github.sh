#!/bin/bash

# Script to push to GitHub repository: gemini_v4_opt_api
# Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME

if [ -z "$1" ]; then
    echo "Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Example: ./push_to_github.sh johndoe"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="gemini_v4_opt_api"

echo "Setting up remote for: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
echo ""

# Check if remote already exists
if git remote get-url origin &>/dev/null; then
    echo "Remote 'origin' already exists. Updating..."
    git remote set-url origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
else
    echo "Adding remote 'origin'..."
    git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
fi

echo ""
echo "Remote configured. Now pushing to GitHub..."
echo ""

# Ensure we're on main branch
git branch -M main

# Push to GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "Repository: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
else
    echo ""
    echo "❌ Push failed. Make sure:"
    echo "1. The repository '${REPO_NAME}' exists on GitHub"
    echo "2. You have access to push to it"
    echo "3. You're authenticated with GitHub (git credential or SSH key)"
fi

