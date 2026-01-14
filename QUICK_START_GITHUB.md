# 🚀 Quick Start: Push to GitHub

Follow these steps to get The Logbook into your GitHub repository.

## Prerequisites

- ✅ GitHub repository created: https://github.com/thegspiro/the-logbook
- ✅ Git installed on your computer
- ✅ GitHub account configured (`git config --global user.name` and `user.email`)

## Step-by-Step Commands

### 1. Navigate to Your Project Location

```bash
# Example: if you saved the project in Downloads
cd ~/Downloads/intranet-platform

# OR wherever you have the project files
```

### 2. Initialize Git Repository (if not already)

```bash
# Initialize git
git init

# Set main branch
git branch -M main
```

### 3. Add Remote Repository

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/thegspiro/the-logbook.git

# Verify it was added
git remote -v
```

### 4. Create .gitignore (Already Done!)

The `.gitignore` file is already in place and will prevent sensitive files from being committed.

**Important files that will NOT be committed:**
- `.env` (your secrets)
- `node_modules/`
- `venv/` or `__pycache__/`
- Database files
- Uploaded files
- Logs

### 5. Stage All Files

```bash
# Add all files
git add .

# Check what will be committed
git status
```

You should see files like:
```
On branch main
Changes to be committed:
  new file:   .gitignore
  new file:   README.md
  new file:   docker-compose.yml
  new file:   backend/main.py
  new file:   frontend/package.json
  ...
```

### 6. Create Initial Commit

```bash
git commit -m "Initial commit: The Logbook platform

- Python backend with FastAPI
- React frontend with TypeScript
- Docker configuration
- Database migrations
- Security features (tamper-proof audit logs, RBAC)
- Module system (training, compliance, scheduling, etc.)
- Integration framework
- Comprehensive documentation"
```

### 7. Push to GitHub

```bash
# Push to main branch
git push -u origin main
```

If this is your first push and the repository isn't empty, you might need:

```bash
# Force push (only if repository has initial commits you want to replace)
git push -u origin main --force
```

### 8. Verify on GitHub

1. Go to https://github.com/thegspiro/the-logbook
2. You should see all your files!
3. Check that `.env` is NOT there (good!)
4. Verify README.md displays properly

---

## 🔐 Next Steps: Set Up Secrets

After pushing, configure GitHub Secrets for CI/CD:

### Navigate to Secrets

1. Go to repository **Settings**
2. Click **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Required Secrets

```bash
# Generate these locally:

# SECRET_KEY (for JWT tokens)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# ENCRYPTION_KEY (for data encryption)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Strong database password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Add These Secrets

| Secret Name | Example Value | Purpose |
|-------------|---------------|---------|
| `DB_PASSWORD` | `aB3$xYz...` | Database password |
| `SECRET_KEY` | `abc123...` | JWT signing key |
| `ENCRYPTION_KEY` | `1a2b3c...` | Data encryption |
| `REDIS_PASSWORD` | `xyz789...` | Redis password |

---

## 🏷️ Create Your First Release

```bash
# Tag version 1.0.0
git tag -a v1.0.0 -m "Initial release of The Logbook

Features:
- Modular architecture
- Tamper-proof audit logging
- User management with RBAC
- Training & certification tracking
- Compliance management
- Shift scheduling
- Document management
- And more!"

# Push the tag
git push origin v1.0.0
```

Then on GitHub:
1. Go to **Releases** → **Draft a new release**
2. Choose tag `v1.0.0`
3. Title: "The Logbook v1.0.0 - Initial Release"
4. Add release notes
5. Publish

---

## 🌿 Create Development Branch

```bash
# Create develop branch
git checkout -b develop

# Push to GitHub
git push -u origin develop
```

Now you can work on features in separate branches:

```bash
# Create feature branch
git checkout -b feature/training-improvements develop

# ... make changes ...

git add .
git commit -m "feat: improve training module"
git push -u origin feature/training-improvements

# Create pull request on GitHub
```

---

## 🔄 Enable GitHub Actions

1. Go to **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**
3. Workflows will run automatically on push

---

## 📊 Monitor Your Repository

### Add Status Badges to README

Edit `README.md` and add at the top:

```markdown
# The Logbook

[![CI/CD](https://github.com/thegspiro/the-logbook/actions/workflows/ci.yml/badge.svg)](https://github.com/thegspiro/the-logbook/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> A secure, modular intranet platform for fire departments and emergency services
```

Commit and push:

```bash
git add README.md
git commit -m "docs: add status badges"
git push
```

---

## ✅ Verification Checklist

After pushing, verify:

- [ ] All files visible on GitHub
- [ ] `.env` is NOT in repository
- [ ] README displays correctly
- [ ] GitHub Actions are enabled
- [ ] Secrets are configured
- [ ] Branch protection set up (optional)
- [ ] License file present
- [ ] Contributing guidelines visible

---

## 🐛 Troubleshooting

### Problem: "Repository not empty" error

```bash
# Pull first, then push
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Problem: Large files rejected

```bash
# Find large files
find . -type f -size +50M

# Remove from git if needed
git rm --cached path/to/large/file
```

### Problem: Wrong remote URL

```bash
# Check current remote
git remote -v

# Change if wrong
git remote set-url origin https://github.com/thegspiro/the-logbook.git
```

### Problem: Need to undo last commit

```bash
# Undo last commit but keep changes
git reset --soft HEAD~1

# OR undo completely
git reset --hard HEAD~1
```

---

## 🎉 Success!

Once pushed, your repository is live at:
**https://github.com/thegspiro/the-logbook**

Share it with:
```
git clone https://github.com/thegspiro/the-logbook.git
```

---

## 📚 What's Next?

1. **Read**: `GITHUB_SETUP.md` for detailed configuration
2. **Configure**: Set up branch protection rules
3. **Enable**: Security scanning and Dependabot
4. **Create**: Issues for features you want to add
5. **Build**: Start developing your modules!

---

**Need help?** Check `GITHUB_SETUP.md` for comprehensive guidance.

**Ready to code?** See `backend/PYTHON_GUIDE.md` for development workflow.
