# Dockerfile

FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Create logs directory at container root for file-based logging
RUN mkdir -p /logs

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full source code, including app/
COPY . .

# Run the FastAPI app from app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
