# Git History Cleanup Script
# This will delete all git history and create a fresh repository

Write-Host "Starting git history cleanup..." -ForegroundColor Yellow

# Backup current branch name
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Remove .git directory
Write-Host "Removing old git history..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .git

# Initialize new repository
Write-Host "Initializing fresh repository..." -ForegroundColor Yellow
git init

# Add all files
Write-Host "Adding all files..." -ForegroundColor Yellow
git add .

# Create initial commit
Write-Host "Creating clean initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit with secure configuration

- All API keys moved to environment variables
- Comprehensive documentation (README, CONTRIBUTING, SECURITY)
- Multi-platform academic career tracking system
- AI-powered paper recommendation engine"

# Rename to main branch
Write-Host "Setting branch to main..." -ForegroundColor Yellow
git branch -M main

# Add remote (replace with your actual GitHub URL)
Write-Host "Adding remote origin..." -ForegroundColor Yellow
git remote add origin https://github.com/YavuzSelimFit/AcademicEye-ODTU.git

Write-Host "`nGit history cleaned successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Go to GitHub and DELETE the old repository" -ForegroundColor White
Write-Host "2. Create a NEW repository with the same name: AcademicEye-ODTU" -ForegroundColor White
Write-Host "3. Run: git push -u origin main --force" -ForegroundColor White
Write-Host "`nOr if you want to force push to existing repo (WARNING: destructive):" -ForegroundColor Yellow
Write-Host "git push -u origin main --force" -ForegroundColor Red
