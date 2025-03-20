# Stage 1: Builder
FROM python:3.12.6-slim AS builder
WORKDIR /app

# Install system dependencies (no Rust needed now)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Stage 2: Final Image
FROM python:3.12.6-slim
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Set path to venv in the final image
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN adduser --disabled-password --no-create-home appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000