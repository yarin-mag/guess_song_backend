# Project Setup & Usage Guide

This guide outlines how to install, run, and debug the project on a Windows machine. It assumes you are using PowerShell and have Python installed.

---

## 📦 First-Time Setup (Windows)

Run the following commands from the root directory of the project:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Clean previous artifacts (if any)
python scripts/clean.py

# Start the API
python scripts/run_api.py


## Generate new Secret API keys:
# INTERNAL_API_KEY (32 bytes, base64url, prefixed)
node -e "const c=require('crypto'); console.log('INTERNAL_API_KEY=aipk_'+c.randomBytes(32).toString('base64url'))"

# MICRO_JWT_SECRET (64 bytes, base64url, prefixed)
node -e "const c=require('crypto'); console.log('MICRO_JWT_SECRET=hs256_'+c.randomBytes(64).toString('base64url'))"
