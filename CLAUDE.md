# FlowPlane Trading Platform - Project Context for Claude

## Project Overview
This is the FlowPlane Trading Platform - an AI-powered personal trading system that autonomously discovers and validates institutional-grade trading strategies.

## Documentation Structure

### Key Documentation Folders
- `/docs/flowplane/` - Main documentation root
  - `00-misc/` - UX guidelines, aesthetics, and project context
  - `20-scope/` - Project scope, requirements, and architecture
  - `30-refinement/` - Feature registry, story registry, requirements catalog
  - `40-design/` - UX specifications and technical design documents
  - `50-implementation/` - **Implementation instructions (most important for building)**

### Implementation Instructions Format
- **50-20XX files**: High-level implementation plans for each feature/user story
- **50-30XX files**: Detailed step-by-step implementation instructions
  - These reference other documents throughout the `/docs/` folder structure
  - Must read referenced documents to understand full context

### Feature/User Story Naming Convention
- **F001-F006**: Features 1-6 (AI Strategy Discovery, Code Generation, Portfolio Management, Validation, Insights, Web Command Center)
- **US001-US00X**: User stories within each feature
- Files are named with pattern: `50-XXXX-FXXX-USXXX-[plan|file-XX].md`

## Important Context
1. The project uses a structured documentation approach with cross-references
2. Implementation files in `50-implementation/` contain the actual build instructions
3. These implementation files reference specifications in other folders (20-scope, 30-refinement, 40-design)
4. Must read both the plan files (50-20XX) and detailed implementation files (50-30XX) together

## Technology Stack Summary
- **Frontend**: Next.js 14+ with TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 with TimescaleDB
- **Market Data**: Polygon.io
- **Broker**: Alpaca
- **Backtesting**: Vectorbt
- **Hosting**: Railway.app

## Development Environment
- **Docker**: Docker Desktop on Windows connected to WSL2
- **OS**: Windows with WSL2 (Linux subsystem)
- **Container Orchestration**: Docker Compose for local development

## Current Status
- Documentation is complete and ready for implementation
- Architecture and scope are fully aligned
- Implementation instructions are available in `/docs/flowplane/50-implementation/`

## Build Process
To build this project:
1. Start with the plan files in `50-implementation/` (50-20XX series)
2. Follow the detailed steps in the corresponding 50-30XX files
3. Reference other documents as needed from the `/docs/` structure
4. Each feature should be built following the F001-F006 sequence

## Notes for Future Sessions
- Always check this file first when returning to the project
- The implementation folder contains step-by-step instructions
- Cross-reference with other documentation folders as needed
- Follow the structured approach defined in the implementation files

## Development Best Practices
- **Track progress against implementation files**: As each task is completed, verify against the requirements in 50-XXXX files
- **Make regular commits**: Commit after completing each logical unit of work (e.g., after setting up a service, completing an API endpoint, etc.)
- **Follow the naming conventions**: Use the exact file paths and component names specified in the implementation guides
- **Validate each step**: Run the validation criteria specified in each task before moving to the next

## Implementation Progress

### ✅ Completed: Slice 0 - Development Foundation (F001-US001)
**Date**: 2025-08-17
**Tasks Completed**:

1. **Docker Environment Setup** ✅
   - Created `docker-compose.yml` with all services
   - PostgreSQL 16 with TimescaleDB extension
   - Redis 7 for caching and task queuing
   - Full service orchestration

2. **Backend Structure (FastAPI)** ✅
   - Created `/backend/app/` structure
   - Main FastAPI application with WebSocket support
   - API router structure (`/api/v1/`)
   - Core configuration with environment variables
   - Database setup with async SQLAlchemy

3. **Frontend Structure (Next.js)** ✅
   - Created `/frontend/src/` structure
   - Next.js 14 with TypeScript
   - Tailwind CSS configuration
   - Basic landing page

4. **Database Models** ✅
   - `Opportunity` model for discovered opportunities
   - `Strategy` model for trading strategies
   - `ScanResult` model for scan history
   - Alembic migrations configured

5. **Celery Async Tasks** ✅
   - Celery app configuration
   - Scanner tasks for market scanning
   - Analysis tasks for correlation
   - Beat scheduler for periodic tasks

6. **Polygon.io Integration** ✅
   - Official `polygon-api-client` SDK integrated
   - REST client for historical data
   - WebSocket support for real-time streaming
   - Market scanning methods implemented
   - Methods: `get_tickers()`, `get_aggregates()`, `get_last_trade()`, etc.

7. **API Endpoints** ✅
   - `/api/v1/scanner/` - Market scanning endpoints
   - `/api/v1/strategies/` - Strategy management
   - `/api/v1/portfolio/` - Portfolio overview

8. **Testing Framework** ✅
   - Pytest configuration for backend
   - Jest configuration for frontend
   - Test fixtures and sample tests

9. **Environment Configuration** ✅
   - `.env.example` with all required variables
   - Docker Compose environment setup
   - Secrets management structure

10. **Documentation** ✅
    - `SETUP.md` with detailed setup instructions
    - `.gitignore` for proper version control
    - This CLAUDE.md file for context

### ✅ Completed: Slice 1 - Core Happy Path (F001-US001)
**Date**: 2025-08-17
**Tasks Completed**: 11/11 tasks
- Implemented Polygon.io market data fetching for equities, futures, and FX
- Created inefficiency detection algorithms (7 types)
- Built correlation analysis engine
- Implemented opportunity ranking system
- Created scanner configuration React component
- Built real-time progress indicator with WebSocket
- Developed results table with sortable columns
- Added opportunity detail modal/panel
- Integrated async task processing for scan execution
- Added basic error handling for API failures

### ✅ Completed: Slice 2 - Alternative Flows (F001-US001)
**Date**: 2025-08-17
**Tasks Completed**: 9/9 tasks
- Created configuration presets with 4 default profiles (Aggressive, Conservative, Momentum, Forex)
- Implemented scan scheduler with hourly/daily/weekly options
- Built export functionality (CSV, JSON, clipboard)
- Integrated all components into scanner page
- Fixed compilation errors and UI issues

### 📋 Next Steps: Slice 3 - Error Handling (F001-US001)
According to `50-2001-F001-US001-plan.md`, the next tasks are:
1. Implement rate limit detection and queuing
2. Add automatic retry with exponential backoff
3. Create network connectivity monitoring
4. Build data validation pipeline
5. Add scan timeout controls
6. Implement graceful degradation
7. Create user-friendly error messages
8. Add comprehensive logging

### 🔑 API Keys Status
- **Polygon.io**: ⏳ Needed (get free key at https://polygon.io/)
- **Alpaca**: ⏳ Needed (get paper trading keys at https://alpaca.markets/)
- **OpenAI**: ❌ Not needed yet (Feature 5)

### 📁 Files Created/Modified
- `/docker-compose.yml`
- `/backend/` - Full FastAPI structure
- `/frontend/` - Full Next.js structure
- `/backend/app/services/polygon_service.py` - Complete Polygon integration
- `/backend/app/models/` - All database models
- `/backend/app/tasks/` - Celery task definitions
- `/.env.example` - Environment template
- `/SETUP.md` - Setup instructions
- `/.gitignore` - Version control config