#!/bin/bash

echo "Starting FlowPlane Trading Platform locally..."

# Start Redis (if installed)
if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes
    echo "✓ Redis started"
else
    echo "⚠ Redis not found - install with: sudo apt-get install redis-server"
fi

# Start PostgreSQL (if installed)
if command -v psql &> /dev/null; then
    sudo service postgresql start
    echo "✓ PostgreSQL started"
    
    # Create database
    sudo -u postgres psql -c "CREATE DATABASE flowplane;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER flowplane WITH PASSWORD 'flowplane_dev_password';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flowplane TO flowplane;" 2>/dev/null || true
else
    echo "⚠ PostgreSQL not found - install with: sudo apt-get install postgresql"
fi

# Backend
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements-simple.txt
echo "✓ Backend dependencies installed"

# Run migrations
export DATABASE_URL="postgresql://flowplane:flowplane_dev_password@localhost:5432/flowplane"
alembic upgrade head 2>/dev/null || echo "⚠ Migrations skipped"

# Start backend
uvicorn app.main:app --reload --port 8000 &
echo "✓ Backend started on http://localhost:8000"

# Frontend
cd ../frontend
npm install
echo "✓ Frontend dependencies installed"

npm run dev &
echo "✓ Frontend started on http://localhost:3000"

echo ""
echo "================================"
echo "FlowPlane Trading Platform Ready!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
wait