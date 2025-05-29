# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

1. **Never invent information**: Never create emails, team names, companies or personal data. Always use generic placeholders like 'your-email@example.com' or 'Your Name' when necessary. Ask first if specific information is needed.

2. **Only implement what's requested**: Don't create code, artifacts, files or features that weren't explicitly requested. Implement only what was asked and strictly necessary to function.

3. **Prefer concise code**: Write minimal, concise code. Whenever possible, write fewer lines while maintaining clarity and functionality. Smaller, more precise and useful code is better than verbose code.

4. **Git branch discipline**: Always check the project's branch structure. If a develop branch exists, use it for development. NEVER do 'git push' to main or prod without explicit authorization. Always ask 'Can I push to [branch]?' before pushing to main branches.

## Commands

**Setup environment with UV (recommended - 100x faster than pip):**
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (UV creates venv automatically)
uv sync

# Run development server
uv run python main.py
```

**Alternative setup with pip:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Production mode:**
```bash
# With UV
uv run gunicorn main:server

# With traditional setup
gunicorn main:server
```

**Manage dependencies:**
```bash
# Add dependency
uv add package-name

# Remove dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade
```

## Architecture

This is a Plotly Dash dashboard application structured for Tiny ERP integration:

- **main.py**: Entry point containing Dash app initialization, routing logic, and authentication callbacks
- **app/auth.py**: Login interface with hardcoded credentials (admin/admin123)
- **app/dashboard.py**: Dashboard layout with KPI cards and charts using sample data

The app uses session-based authentication via `dcc.Store` and supports automatic deployment to Railway from both `main` (production) and `develop` (testing) branches.

## Key Development Notes

1. **Naming conflict resolved**: The app was renamed from `app.py` to `main.py` to avoid import conflicts with the `app/` directory
2. **Deployment**: Uses `gunicorn main:server` (not `python main.py`) for Railway/production
3. **Port configuration**: Reads from PORT environment variable, defaults to 8050
4. **Current state**: Dashboard displays sample data only - Tiny ERP integration not yet implemented

## Deployment Configuration

- **Procfile**: `web: gunicorn main:server`
- **railway.json**: Specifies NIXPACKS builder and start command
- Auto-deploys on push to GitHub branches