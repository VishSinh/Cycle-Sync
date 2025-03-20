# Stage 1: Builder
FROM python:3.12.6-slim AS builder
WORKDIR /app

# Install only required system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    rm -rf ~/.cache/pip

# Stage 2: Final Image
FROM python:3.12.6-slim AS final
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=period_tracking_BE.settings \
    DJANGO_DEBUG=False

# Copy application code
COPY . .

# Collect static files during build time
RUN python manage.py collectstatic --noinput

# Create a non-root user
RUN adduser --disabled-password --gecos "" --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Production web server command
CMD ["gunicorn", "period_tracking_BE.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]