#!/bin/bash

# Local development startup script (without Docker)
echo "Starting FlowPlane Trading Platform locally..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    sudo service postgresql start
fi

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "Redis not found. Installing..."
    sudo apt-get install -y redis-server
fi

# Start Redis
echo "Starting Redis..."
redis-server --daemonize yes

# Setup Python virtual environment
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Create database if it doesn't exist
sudo -u postgres psql -c "CREATE DATABASE flowplane;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER flowplane WITH PASSWORD 'flowplane_dev_password';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flowplane TO flowplane;" 2>/dev/null || true

# Run migrations
alembic upgrade head

# Start FastAPI in background
echo "Starting FastAPI backend..."
uvicorn app.main:app --reload --port 8000 &

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info &

# Start Celery beat in background
echo "Starting Celery beat..."
celery -A app.tasks.celery_app beat --loglevel=info &

cd ../frontend

# Install Node dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start Next.js
echo "Starting Next.js frontend..."
npm run dev

echo ""
echo "FlowPlane Trading Platform is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"