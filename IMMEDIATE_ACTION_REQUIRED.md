# CRITICAL: Immediate Actions Required

## Security Breach Summary

GitGuardian detected 2 exposed API keys in your GitHub repository:

1. **Scopus API Key**: `1eadcb2954e012a0481889a8aa9a0aff`
2. **Google Gemini API Key**: `AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w`

**Status**: Keys removed from code BUT still in git history

---

## Step 1: Revoke Exposed Keys IMMEDIATELY

### Scopus API (Priority 1)
1. Go to: https://dev.elsevier.com/
2. Login and navigate to "My API Keys"
3. Find key: `1eadcb2954e012a0481889a8aa9a0aff`
4. **DELETE** this key
5. Generate new key
6. Add to `.env`: `SCOPUS_API_KEY=your_new_key`

### Google Gemini API (Priority 1)
1. Go to: https://makersuite.google.com/app/apikey
2. Find key starting with: `AIzaSyAduGguEQIlcIRjODHmqqV0yTvG8-ja56w`
3. **DELETE** this key
4. Create new key
5. Add to `.env`: `GEMINI_API_KEY=your_new_key`

---

## Step 2: Clean Git History

Keys are still in git history. Anyone who cloned your repo can see them.

### Option A: Simple (GitHub Web)

1. Go to your GitHub repo settings
2. Click "Danger Zone" > "Change repository visibility"
3. Make it Private temporarily
4. Download and install BFG: https://rtyley.github.io/bfg-repo-cleaner/

```bash
# Clone a fresh copy
git clone --mirror https://github.com/YavuzSelimFit/AcademicEye-ODTU.git

# Run BFG to remove secrets
java -jar bfg.jar --replace-text secrets-to-remove.txt AcademicEye-ODTU.git

# Clean up
cd AcademicEye-ODTU.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force
```

### Option B: Delete and Recreate Repository (Easiest)

1. Download your current code
2. Delete the GitHub repository
3. Create new repository with same name
4. Initialize fresh git:

```bash
cd d:\Project314\AcademicEye
rm -rf .git
git init
git add .
git commit -m "Initial commit with secure configuration"
git branch -M main
git remote add origin https://github.com/YavuzSelimFit/AcademicEye-ODTU.git
git push -u origin main --force
```

---

## Step 3: Verify .env is Not Tracked

```bash
# Check git status
git status

# If .env appears, remove it
git rm --cached .env
git commit -m "security: ensure .env is not tracked"
git push
```

---

## Step 4: Update Your Keys Locally

After revoking and generating new keys, update your `.env` file:

```bash
# Edit .env
SCOPUS_API_KEY=your_new_scopus_key_here
GEMINI_API_KEY=your_new_gemini_key_here
```

Test that everything works:

```bash
python app.py
```

---

## What Was Fixed

- Removed hardcoded Scopus key from `modules/career_engine/scopus_bot.py`
- Removed hardcoded Google key from `modules/feed_engine/check_models.py`
- Both now use environment variables
- Created SECURITY.md documentation
- Committed fix with message: "security: remove hardcoded API keys..."

---

## Timeline

- **Dec 25, 2025**: Keys committed to repository
- **Jan 1, 2026 20:04**: GitGuardian alert
- **Jan 1, 2026 20:10**: Keys removed from code (CURRENT)
- **NEXT**: You must revoke keys and clean history

---

## Files to Delete After Cleanup

```bash
# After fixing everything, remove these files:
rm secrets-to-remove.txt
rm IMMEDIATE_ACTION_REQUIRED.md
git add .
git commit -m "chore: remove security incident response files"
```

---

## Questions?

Read full details in SECURITY.md

**DO NOT SKIP KEY REVOCATION** - The old keys are compromised and publicly visible in git history.
