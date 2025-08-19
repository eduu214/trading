# AlphaStrat Trading Intelligence
An AI-powered personal trading system that autonomously discovers and validates institutional-grade trading strategies

## Overview
AlphaStrat is an intelligent trading platform that acts as your institutional-grade research team—autonomously discovering market opportunities, rigorously validating them through sophisticated testing, and presenting only proven strategies with clear explanations of why they work and how to safely implement them.

Unlike traditional platforms that require existing trading expertise and strategy ideas, AlphaStrat handles the complex analysis and presents clear insights, enabling ambitious traders to achieve institutional-quality results without requiring institutional knowledge.

## Key Features

### 🔍 AI Strategy Discovery Engine
- **Multi-Market Scanning**: Continuously analyzes US equities, FX pairs, and futures markets for exploitable inefficiencies
- **Intelligent Complexity Optimization**: Automatically determines the optimal strategy sophistication level for best risk-adjusted returns
- **Diversification Focus**: Prioritizes finding uncorrelated strategies to build robust portfolios that work across market conditions

### 🚀 Automated Code Generation & Execution
- **Multi-Platform Support**: Generates executable code for Alpaca, TradingView Pine Script, and generic Python
- **Built-in Safeguards**: Embeds comprehensive safety checks including position limits, loss circuit breakers, and sanity validations
- **Seamless Production Bridge**: Ensures live performance matches backtests through careful paper trading transitions

### 📊 Intelligent Portfolio Management
- **Correlation-Based Construction**: Optimally allocates capital based on real-time correlation dynamics
- **Lifecycle Management**: Automates strategy rotation, promoting new strategies when opportunities arise and retiring those showing alpha decay
- **Risk Parity Allocation**: Uses modern portfolio theory to maximize risk-adjusted returns

### ✅ Institutional-Grade Validation
- **Asset-Specific Testing**: Applies appropriate validation rules for each market's unique characteristics
- **Complexity-Adjusted Rigor**: More complex strategies undergo exponentially more validation to prevent overfitting
- **Multiple Validation Layers**: Combines historical backtesting, Monte Carlo simulations, and paper trading verification

### 💡 Clear Strategy Insights
- **Plain English Explanations**: Every strategy comes with clear explanations of why it works and when it might fail
- **Market Research Integration**: Automatically aggregates insights from reputable sources to provide context
- **Performance Benchmarking**: Shows how strategies compare to simple buy-and-hold and relevant indices

### 🖥️ Intuitive Web Command Center
- **Clean Dashboard**: Card-based layout with visual correlation maps and real-time P&L tracking
- **Progressive Disclosure**: Hides complexity until needed, with tooltips explaining all technical terms
- **One-Click Operations**: Deploy strategies, rebalance portfolios, and manage risk with simple actions

## Technology Stack

### Core Infrastructure
- **Frontend**: Next.js 14+ with TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 with TimescaleDB
- **Authentication**: Clerk managed auth service
- **Hosting**: Railway.app PaaS platform

### Market Data & Execution
- **Market Data**: Polygon.io (comprehensive coverage with excellent API)
- **Broker Integration**: Alpaca (commission-free with paper trading)
- **Backtesting Engine**: Vectorbt (100x faster than traditional approaches)
- **Portfolio Optimization**: PyPortfolioOpt

### Intelligence Layer
- **Strategy Discovery**: Custom Python algorithms with Celery workers
- **Natural Language**: OpenAI API for strategy explanations
- **Research Aggregation**: Web scraping with BeautifulSoup/Scrapy
- **Real-time Processing**: Redis caching with WebSocket updates

## MVP Market Coverage
- **US Equities**: Full coverage via Alpaca
- **Foreign Exchange**: Major pairs available through Alpaca
- **Futures**: CME micro contracts (limited availability)
- **Coming Soon**: Full futures coverage, international markets, options strategies

## Performance Targets
- **Strategy Discovery**: 20+ validated strategies monthly
- **Portfolio Size**: Support for 50-100 concurrent strategies
- **Processing Scale**: 1000+ symbols per scan cycle
- **Execution Speed**: Sub-second order placement
- **Backtest Duration**: 5-120 minutes with progress indicators

## Getting Started
*[Setup instructions will be added as development progresses]*

## Testing

The AlphaStrat project maintains comprehensive test coverage across all components:

### Test Organization
- **Backend Tests**: `backend/tests/` - FastAPI endpoints, services, and database tests
- **Frontend Tests**: `frontend/src/__tests__/` - React components and integration tests  
- **Integration Tests**: `tests/integration/` - End-to-end testing across services
- **Test Scripts**: `tests/scripts/` - Automated test execution and validation scripts
- **Test Documentation**: `tests/docs/` - Test reports and summaries

### Running Tests
```bash
# Backend tests
cd backend && pytest

# Frontend tests  
cd frontend && npm test

# Integration tests
./tests/scripts/test_complexity_api.sh
```

For detailed testing documentation, see [`tests/README.md`](tests/README.md).

## Project Status
Currently in active development. The system architecture is fully designed and aligned with comprehensive scope requirements. Implementation focuses on delivering a robust MVP with clear paths for future expansion.

## Documentation
Detailed technical documentation is available in the `/docs/flowplane/` directory:
- `20-1001-scope.md`: Complete feature specifications and user stories
- `20-2001-architecture.md`: Technical architecture and implementation details
- `20-3001-alignment-analysis.md`: Scope-architecture alignment verification

## License
*[License information to be determined]*