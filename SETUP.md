# FlowPlane Trading Platform - Setup Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (if running locally without Docker)
- Redis 7+ (if running locally without Docker)

## Quick Start with Docker

1. **Clone the repository and navigate to the project directory**
```bash
cd /home/jack/dev/trading
```

2. **Copy environment variables**
```bash
cp .env.example .env
```

3. **Configure your API keys in `.env`**
- Get a Polygon.io API key from https://polygon.io/
- Get Alpaca API keys from https://alpaca.markets/
- Get an OpenAI API key from https://platform.openai.com/

4. **Start all services with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL with TimescaleDB
- Redis
- FastAPI backend
- Celery workers
- Next.js frontend

5. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Local Development Setup (Without Docker)

### Backend Setup

1. **Create Python virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL with TimescaleDB**
```bash
# Install TimescaleDB extension for PostgreSQL 16
# Follow instructions at https://docs.timescale.com/install/latest/

# Create database
createdb flowplane
psql -d flowplane -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the backend server**
```bash
uvicorn app.main:app --reload --port 8000
```

6. **Start Celery workers (in separate terminals)**
```bash
# Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Start the development server**
```bash
npm run dev
```

3. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Running Tests

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Project Structure

```
trading/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic services
│   │   └── tasks/        # Celery async tasks
│   ├── alembic/          # Database migrations
│   ├── tests/            # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js app directory
│   │   ├── components/   # React components
│   │   ├── lib/          # Utility functions
│   │   └── __tests__/    # Frontend tests
│   └── package.json
├── docs/                 # Project documentation
└── docker-compose.yml

```

## Common Commands

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild services
docker-compose build
```

### Database Commands
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Development Commands
```bash
# Backend formatting
cd backend && black . && ruff check .

# Frontend linting
cd frontend && npm run lint

# Run all tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

## Troubleshooting

1. **Port already in use**: Make sure ports 3000, 8000, 5432, and 6379 are not in use
2. **Database connection errors**: Ensure PostgreSQL is running and credentials are correct
3. **API key errors**: Verify all API keys in `.env` are valid
4. **Docker issues**: Try `docker-compose down -v` and rebuild with `docker-compose build --no-cache`

## Next Steps

After setup is complete, you can:
1. Access the dashboard at http://localhost:3000/dashboard
2. Configure market scanning parameters
3. Start discovering trading opportunities
4. Review the API documentation at http://localhost:8000/docs