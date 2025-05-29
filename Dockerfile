# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file (keep for Railway compatibility)
COPY requirements.txt .

# Install dependencies with pip (Railway-compatible approach)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8050

# Set environment variables
ENV PORT=8050
ENV DEBUG=False

# Run with gunicorn
CMD ["gunicorn", "main:server", "--bind", "0.0.0.0:8050"]