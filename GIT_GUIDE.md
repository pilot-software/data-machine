# ✅ Git Commit Checklist

## Files to COMMIT (Code & Docs)

### Core Application
- ✅ `app/` - All Python code
- ✅ `scripts/` - ETL and setup scripts
- ✅ `requirements.txt` - Dependencies
- ✅ `.env.example` - Environment template

### Scripts
- ✅ `install.sh` - One-command setup
- ✅ `start.sh` - Start server
- ✅ `stop.sh` - Stop server
- ✅ `restart.sh` - Restart server
- ✅ `status.sh` - Check status
- ✅ `test_all.sh` - Test suite

### Documentation
- ✅ `README.md` - Main documentation
- ✅ `DEPLOYMENT.md` - Deployment guide
- ✅ `WORKFLOW.md` - Usage flow
- ✅ `USER_GUIDE.md` - API usage
- ✅ `LLM_SETUP_GUIDE.md` - AI setup
- ✅ `SNOMED_QUICKSTART.md` - SNOMED guide
- ✅ All other `.md` files

### Configuration
- ✅ `.gitignore` - Git ignore rules
- ✅ `.env.example` - Environment template

---

## Files to IGNORE (Data & Logs)

### Large Data Files (Download separately)
- ❌ `CommonDrugCodesForIndia_FlatFilePackage/` (500MB+)
- ❌ `SnomedCT_IndiaDrugExtensionRF2_*/` (1GB+)
- ❌ `data/*.csv` - Data files
- ❌ `data/*.json` - Data files

### Generated Files
- ❌ `logs/` - Log files
- ❌ `__pycache__/` - Python cache
- ❌ `*.pyc` - Compiled Python
- ❌ `nohup.out` - Background process logs

### Environment
- ❌ `.env` - Local environment (has secrets)
- ❌ `venv/` - Virtual environment

---

## Quick Commands

```bash
# Check what will be committed
git status

# Add all code files
git add app/ scripts/ *.sh *.md requirements.txt .gitignore .env.example

# Commit
git commit -m "feat: Complete HMS Terminology Service with AI diagnosis"

# Push
git push origin main
```

---

## Data Files Setup (For New Clones)

After cloning, download data separately:

1. **CommonDrugCodesForIndia_FlatFilePackage/**
   - Download from: https://www.nrces.in/standards/snomed-ct
   - Place in project root

2. **SnomedCT_IndiaDrugExtensionRF2_*/**
   - Download from: https://www.nrces.in/standards/snomed-ct
   - Place in project root

3. Run setup:
   ```bash
   ./install.sh
   ```

---

## Commit Message Format

```bash
# Feature
git commit -m "feat: Add drug classification API"

# Fix
git commit -m "fix: Resolve ICD code search issue"

# Documentation
git commit -m "docs: Update deployment guide"

# Refactor
git commit -m "refactor: Optimize database queries"
```
