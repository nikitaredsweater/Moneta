# Dockerfile

FROM python:3.13-slim AS base

# Set working directory to /app
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base AS development

# Copy source code
COPY . .

# Command to run the application in development mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

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

# Command to run the application in production mode
# CMD ["fastapi", "dev", "app/main.py"]
# Command to run the application in production mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
