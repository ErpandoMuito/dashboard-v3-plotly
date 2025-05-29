# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

1. **Never invent information**: Never create emails, team names, companies or personal data. Always use generic placeholders like 'your-email@example.com' or 'Your Name' when necessary. Ask first if specific information is needed.

2. **Only implement what's requested**: Don't create code, artifacts, files or features that weren't explicitly requested. Implement only what was asked and strictly necessary to function.

3. **Prefer concise code**: Write minimal, concise code. Whenever possible, write fewer lines while maintaining clarity and functionality. Smaller, more precise and useful code is better than verbose code.

4. **Git branch discipline**: Always check the project's branch structure. If a develop branch exists, use it for development. Push to develop is always allowed without asking. NEVER do 'git push' to main or prod without explicit authorization. Always ask 'Can I push to main?' before pushing to production branches.

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
- **Custom Domain**: Set `APP_DOMAIN=pxn.app.br` in Railway environment variables
- **OAuth Redirect**: The redirect URI must match the domain used (update in Tiny OAuth settings if domain changes)

## Tiny API V3 Reference

API Base URL: https://api.tiny.com.br/public-api/v3

### Authentication Flow
1. **Authorization**: GET https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth
   - Parameters: client_id, redirect_uri, scope=openid, response_type=code
2. **Token Exchange**: POST https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token
   - Grant type: authorization_code
   - Returns: access_token (4h), refresh_token (24h)
3. **Token Refresh**: Same endpoint with grant_type=refresh_token

### Key Endpoints

**1. Produtos (Products)**
- GET /produtos - List products
  - Query params: nome, codigo, gtin, situacao, limit, offset
- GET /produtos/{idProduto} - Get product by ID
- POST /produtos - Create product
- PUT /produtos/{idProduto}/preco - Update price

**2. Estoque (Stock/Inventory)**
- GET /estoque/{idProduto} - Get product stock
- POST /estoque/{idProduto} - Update stock (types: B=Balance, E=Entry, S=Exit)

**3. Notas Fiscais (Invoices)**
- GET /notas - List invoices
- GET /notas/{idNota} - Get invoice details
- GET /notas/{idNota}/xml - Get XML
- POST /notas/{idNota}/emitir - Issue invoice
- POST /notas/xml - Import XML (multipart/form-data)

**4. Pedidos (Orders)**
- POST /pedidos - Create order
- POST /pedidos/{idPedido}/gerar-nota-fiscal - Generate invoice from order

### Authentication Headers
All requests require:
- Authorization: Bearer {access_token}
- Accept: application/json

### Important Notes
- IDs are always integers
- Dates format: YYYY-MM-DD
- Monetary values are floats
- Default pagination: 100 items
- SKU must be unique