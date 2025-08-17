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

## Current Implementation Status

### 📋 Active Implementation Files
- **Main Plan**: `/docs/flowplane/50-implementation/50-2001-F001-US001-plan.md`
- **Detailed Tasks**: 
  - `/docs/flowplane/50-implementation/50-3001-F001-US001-file-01.md`
  - `/docs/flowplane/50-implementation/50-3001-F001-US001-file-02.md`
- **Progress Summary**: `/PROGRESS_SUMMARY.md`

### ✅ Current Status: F001-US001 Complete
- **Feature**: AI Strategy Discovery Engine (F001-US001)
- **Status**: All 38 original tasks completed across 4 slices + 8 additional scope creep tasks (2025-08-17)
- **Next Phase**: Ready for F002 or other features

### 🔑 API Keys Status
- **Polygon.io**: ⏳ Needed (get free key at https://polygon.io/)
- **Alpaca**: ⏳ Needed (get paper trading keys at https://alpaca.markets/)
- **OpenAI**: ❌ Not needed yet (Feature 5)

## Important Implementation Constraint
**CRITICAL**: DO NOT make up additional tasks, steps, stories, etc. YOU MUST follow the plans and tasks in the flowplane docs exactly as documented. Always update the 50-XXXX files at the end of every step to mark progress.