FROM python:3.12.6-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies, PostgreSQL client libraries, and Rust
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

# Add Rust to PATH explicitly
ENV PATH="/root/.cargo/bin:$PATH"

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Create non-root user
RUN adduser --disabled-password --no-create-home appuser

# Copy project files
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000