FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ==========================================
# HUGGING FACE SPACES CONFIGURATION
# ==========================================
# 1. Create a non-root user (ID 1000) as required by HF Spaces
# 2. Grant permissions to /app so SQLite and ChromaDB can save data
RUN useradd -m -u 1000 user && \
    chown -R user:user /app

USER user

# Hugging Face Spaces uses port 7860 by default
EXPOSE 7860

# Health check (Start period increased to 120s for ChromaDB model download)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:7860/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
