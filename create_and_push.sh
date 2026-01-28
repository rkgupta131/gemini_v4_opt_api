#!/bin/bash

# Script to authenticate with GitHub and create repository

set -e

REPO_NAME="gemini_v4_opt_api"
GITHUB_USER="rkgupta131"

echo "🚀 Creating GitHub repository: $REPO_NAME"
echo ""

# Check if already authenticated
if gh auth status &>/dev/null; then
    echo "✅ Already authenticated with GitHub"
else
    echo "⚠️  Not authenticated. Starting authentication..."
    echo ""
    echo "Please follow these steps:"
    echo "1. Run: gh auth login"
    echo "2. Choose: GitHub.com"
    echo "3. Choose: HTTPS"
    echo "4. Authenticate via browser or token"
    echo ""
    read -p "Press Enter after you've authenticated, or Ctrl+C to cancel..."
    
    # Verify authentication
    if ! gh auth status &>/dev/null; then
        echo "❌ Authentication failed. Please try again."
        exit 1
    fi
fi

echo ""
echo "📦 Creating repository on GitHub..."

# Remove existing remote if it exists and points to wrong URL
if git remote get-url origin &>/dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    EXPECTED_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    if [ "$CURRENT_URL" != "$EXPECTED_URL" ]; then
        echo "Updating remote URL..."
        git remote set-url origin "$EXPECTED_URL"
    fi
fi

# Create repository and push
gh repo create "$REPO_NAME" \
    --private \
    --source=. \
    --remote=origin \
    --push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully created and pushed to GitHub!"
    echo "📍 Repository: https://github.com/${GITHUB_USER}/${REPO_NAME}"
    echo ""
    echo "You can view it at:"
    echo "  https://github.com/${GITHUB_USER}/${REPO_NAME}"
else
    echo ""
    echo "❌ Failed to create repository. Please check:"
    echo "  1. You're authenticated: gh auth status"
    echo "  2. Repository doesn't already exist"
    echo "  3. You have permission to create repos"
    exit 1
fi

