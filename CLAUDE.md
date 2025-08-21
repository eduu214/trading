# AlphaStrat Trading Platform - Project Context for Claude

## Project Overview
This is the AlphaStrat Trading Platform - an AI-powered personal trading system that autonomously discovers and validates institutional-grade trading strategies.

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

### Docker Setup Instructions
1. **Start Containers**: `docker-compose up -d`
2. **Check Status**: `docker-compose ps`
3. **Stop Containers**: `docker-compose down`
4. **Rebuild After Dependencies Change**: `docker-compose up --build -d`
5. **View Logs**: `docker-compose logs [service_name]`

### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

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

## Current Implementation Status

### 📋 Active Implementation Files
- **Previous Feature**: F002-US001 - Strategy Engine with Backtesting (COMPLETE)
- **Current Status**: Determining next feature implementation
- **Progress Summary**: `/PROGRESS_SUMMARY.md`

### ✅ F002-US001 COMPLETE - All 20 Tasks Delivered!
- **Previous**: F001-US001 Complete (38 tasks), F001-US002 Complete (27 tasks)
- **COMPLETED Feature**: F002-US001 - Real Strategy Engine with Backtesting  
- **All Slices**: ✅ Slice 1 (10 tasks), ✅ Slice 2 (3 tasks), ✅ Slice 3 (5 tasks), ✅ Slice 4 (2 tasks)
- **Final Task**: Task 20 - Strategy Approval Workflow with paper trading transition

### 🎯 Major Achievements
- **Strategy Engine**: 3 fully working strategies (RSI, MACD, Bollinger Bands)
- **Backtesting Framework**: Vectorbt integration with real performance metrics
- **WebSocket System**: Real-time progress updates with <1s latency (exceeds requirements)
- **Error Handling**: Comprehensive fallback systems and validation
- **Approval Workflow**: Complete strategy approval with audit trail and paper trading deployment

### 🚧 Next Steps
- **Frontend Integration**: Resolve Next.js compilation issue for main app integration
- **Next Feature**: Determine next feature to implement (F002-US002, F003, F004, F005, or F006)

### 🔑 API Keys Status
- **Polygon.io**: ⏳ Needed (get free key at https://polygon.io/)
- **Alpaca**: ⏳ Needed (get paper trading keys at https://alpaca.markets/)
- **OpenAI**: ❌ Not needed yet (Feature 5)

## Important Implementation Constraint
**CRITICAL**: DO NOT make up additional tasks, steps, stories, etc. YOU MUST follow the plans and tasks in the flowplane docs exactly as documented. Always update the 50-XXXX files at the end of every step to mark progress.