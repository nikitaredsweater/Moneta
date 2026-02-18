FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/app_root/src"

# Create and activate virtual environment
RUN python -m venv /venv

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel setuptools

# Set work directory
WORKDIR /app_root

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base AS development

# Copy source code
COPY . .

# Command to run the application in development mode
# fastapi dev app/main.py
# TODO: Update in the future as needed?
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Lint stage
FROM development AS lint

# Initialize git for pre-commit
RUN git init && git add .

# Run pre-commit hooks
CMD ["pre-commit", "run", "--all-files"]

# Test stage
FROM development AS test

# Run tests
CMD ["pytest", "--durations=0", "-s"]

# Production stage
FROM base AS production

# Copy source code
COPY . .

# Command to run the application in development mode
# fastapi dev app/main.py
# TODO: Untested. Test later
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
