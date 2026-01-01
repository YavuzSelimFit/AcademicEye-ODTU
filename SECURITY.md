# Security Incident Response

## Issue
GitGuardian detected exposed API keys in the repository.

## Exposed Keys

### 1. Scopus API Key
- **File**: `modules/career_engine/scopus_bot.py`
- **Key**: `1eadcb2954e012a0481889a8aa9a0aff`
- **Status**: REVOKED (must regenerate)
- **Fix**: Moved to environment variable `SCOPUS_API_KEY`

### 2. Google Gemini API Key
- **File**: `modules/feed_engine/check_models.py`
- **Key**: `AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w`
- **Status**: REVOKED (must regenerate)
- **Fix**: Removed commented code

## Immediate Actions Required

### 1. Revoke Exposed Keys

#### Scopus API Key
1. Go to https://dev.elsevier.com/
2. Log in to your developer account
3. Navigate to "My API Keys"
4. Revoke the key: `1eadcb2954e012a0481889a8aa9a0aff`
5. Generate a new key
6. Add to `.env` file: `SCOPUS_API_KEY=your_new_key_here`

#### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Log in with your Google account
3. Find the key starting with `AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w`
4. Delete this key
5. Create a new API key
6. Add to `.env` file: `GEMINI_API_KEY=your_new_key_here`

### 2. Clean Git History

The keys are in git history. You need to remove them:

```bash
# Install git filter-repo if not installed
pip install git-filter-repo

# Remove the specific file from history
git filter-repo --path modules/career_engine/scopus_bot.py --invert-paths --force

# Or use BFG Repo-Cleaner (easier)
# Download from: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --replace-text passwords.txt

# Create passwords.txt with:
# 1eadcb2954e012a0481889a8aa9a0aff
# AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w
```

**WARNING**: This rewrites git history. All collaborators must re-clone the repository.

### 3. Force Push to GitHub

```bash
# After cleaning history
git push origin --force --all
git push origin --force --tags
```

### 4. Verify .env is Ignored

```bash
# Check .gitignore contains .env
cat .gitignore | grep "\.env"

# Verify .env is not tracked
git status --ignored

# If .env is tracked, remove it
git rm --cached .env
git commit -m "security: remove .env from tracking"
```

## Code Changes Made

### scopus_bot.py
```python
# Before
API_KEY = "1eadcb2954e012a0481889a8aa9a0aff"

# After
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('SCOPUS_API_KEY')
```

### check_models.py
```python
# Before
# api_key = "AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w"

# After
# Removed commented key entirely
```

## Prevention Measures

### 1. Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Check for potential API keys
if git diff --cached | grep -E "(AIza|AKIA|sk_live|[0-9a-f]{32})"; then
    echo "ERROR: Potential API key detected!"
    echo "Please remove hardcoded credentials."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### 2. Use git-secrets

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
apt-get install git-secrets  # Linux

# Set up for repository
git secrets --install
git secrets --register-aws
```

### 3. Environment Variable Checklist

Before committing, verify:
- [ ] No hardcoded API keys
- [ ] All keys use `os.getenv()` or `os.environ.get()`
- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` has placeholder values only
- [ ] No sensitive data in comments

## Long-term Security

### 1. Use Secret Management
- GitHub Secrets for CI/CD
- HashiCorp Vault for production
- AWS Secrets Manager
- Azure Key Vault

### 2. Rotate Keys Regularly
- Set calendar reminder (every 90 days)
- Document rotation procedure
- Test with new keys before revoking old ones

### 3. Monitor for Leaks
- Enable GitGuardian (already detected this)
- Use GitHub secret scanning
- Set up alerts

## Status

- [x] Identified exposed keys
- [x] Removed from code
- [x] Converted to environment variables
- [ ] Revoked old keys
- [ ] Generated new keys
- [ ] Cleaned git history
- [ ] Force pushed to GitHub
- [ ] Verified repository is clean

## Timeline

- **2025-12-25**: Keys committed to repository
- **2026-01-01 20:04**: GitGuardian alert received
- **2026-01-01 20:05**: Keys removed from code
- **2026-01-01 20:06**: This incident report created

## Notes

The keys were in the repository for approximately 7 days. Assume they are compromised and must be regenerated.
