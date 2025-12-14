# Backend Dockerfile (API, Router, Dashboard)
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Default command (overridden by k8s)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
