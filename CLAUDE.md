# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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