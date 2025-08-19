FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Don't switch to non-root user for now to avoid permission issues
# RUN useradd -m -u 1000 alphastrat && chown -R alphastrat:alphastrat /app
# USER alphastrat

EXPOSE 8000

# Add more verbose logging
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]