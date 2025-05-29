# Use Python 3.12 slim image
FROM python:3.12-slim

# Install UV
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY .python-version .

# Install dependencies with UV (creates venv automatically)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8050

# Set environment variables
ENV PORT=8050
ENV DEBUG=False

# Run with UV
CMD ["uv", "run", "gunicorn", "main:server", "--bind", "0.0.0.0:8050"]