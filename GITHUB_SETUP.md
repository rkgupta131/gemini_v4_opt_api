# GitHub Repository Setup Instructions

## Step 1: Create New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `gemini_v4_opt_api`
3. Description: "Unified streaming API for generating web projects using multiple LLM model families"
4. Choose: **Private** or **Public** (your choice)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Push to GitHub

### Option A: Using the provided script (Easiest)

```bash
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
./push_to_github.sh YOUR_GITHUB_USERNAME
```

### Option B: Manual commands

After creating the repository, run these commands:

```bash
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/gemini_v4_opt_api.git

# Or if using SSH:
git remote add origin git@github.com:YOUR_USERNAME/gemini_v4_opt_api.git

# Ensure branch is named main (already done, but safe to run)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 3: Verify

1. Go to your GitHub repository page
2. Verify all files are present
3. Check that `.env` and sensitive files are NOT visible (they should be in .gitignore)

## Important Notes

### Files Excluded (via .gitignore):
- ✅ `.env` - Environment variables with API keys
- ✅ `output/` - Generated project files
- ✅ `modified_output/` - Modified project files
- ✅ `gemini_v4_opt/` - Virtual environment
- ✅ `*.json` files with secrets (bedrock-router-*.json, n0project-*.json)
- ✅ `google-cloud-sdk/` - Large SDK files
- ✅ `__pycache__/` - Python cache files

### Files Included:
- ✅ All source code (api.py, models/, events/, etc.)
- ✅ Documentation (README.md, API_README.md, etc.)
- ✅ Postman collection
- ✅ Requirements file
- ✅ Configuration files (non-sensitive)

## Security Checklist

Before pushing, ensure:
- [ ] `.env` file is NOT committed (check with `git status`)
- [ ] No API keys in committed files
- [ ] No credentials in code
- [ ] `.gitignore` is working correctly

## Troubleshooting

### If you need to remove a file that was already committed:

```bash
# Remove from git but keep locally
git rm --cached .env

# Commit the removal
git commit -m "Remove sensitive files"

# Push
git push
```

### If you need to update .gitignore:

```bash
# Edit .gitignore
# Then:
git add .gitignore
git commit -m "Update .gitignore"
git push
```

