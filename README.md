# Dashboard V3 - Tiny ERP Integration

Dashboard em Python usando Plotly Dash para integração com Tiny ERP.

## 🚀 Instalação com UV (Recomendado)

Este projeto usa [UV](https://github.com/astral-sh/uv) para gerenciamento de dependências - até 100x mais rápido que pip!

### Instalar UV

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configurar Projeto

```bash
# Clone o repositório
git clone https://github.com/ErpandoMuito/dashboard-v3-plotly.git
cd dashboard-v3-plotly

# Instalar dependências (UV cria venv automaticamente)
uv sync

# Executar em modo desenvolvimento
uv run dev
# ou
uv run python main.py
```

## 📦 Gerenciar Dependências

```bash
# Adicionar nova dependência
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --dev pytest

# Remover dependência
uv remove nome-do-pacote

# Atualizar todas as dependências
uv sync --upgrade
```

## 🛠️ Scripts Disponíveis

```bash
# Executar servidor de desenvolvimento
uv run dev

# Executar servidor de produção
uv run start

# Formatar código
uv run format

# Verificar código
uv run lint

# Executar testes
uv run test
```

## 🐳 Docker

```bash
# Build
docker build -t dashboard-v3 .

# Executar
docker run -p 8050:8050 dashboard-v3
```

## 📝 Instalação Tradicional (pip)

Se preferir usar pip ao invés de UV:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
python main.py
```

## 🔐 Login

- Usuário: admin
- Senha: admin123

## 🚂 Deploy Railway

O projeto está configurado para deploy automático no Railway:
- Branch `main`: Produção
- Branch `develop`: Testes

## 🔧 Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
DEBUG=False
PORT=8050
REDIS_URL=redis://localhost:6379
```