# Dockerfile for reproducible c2s-scale example
FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Install OS-level deps (if needed) and pip tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Use a non-root user for safety (optional)
RUN useradd --create-home appuser || true
USER appuser

# Default command runs the example script
CMD ["python", "example.py"]
