# Feature Technical Architecture - F003: Strategy Portfolio Management

## 1. Architecture Overview

### 1.1 Technical Strategy
F003 leverages PostgreSQL with TimescaleDB for time-series portfolio data, Redis for real-time state management, and PyPortfolioOpt for Modern Portfolio Theory calculations. The feature coordinates with the strategy execution engine (SVC-002) to access individual strategy performance data and uses Celery for background portfolio optimization tasks. Real-time portfolio updates flow through WebSocket connections managed by the notification service (SVC-005).

### 1.2 Key Decisions

- **Decision**: Use Modern Portfolio Theory (Markowitz optimization) for allocation decisions
- **Rationale**: Mathematically proven approach for risk-adjusted returns, industry standard for institutional portfolio management
- **Trade-offs**: Requires historical correlation data vs simpler equal-weight approaches, but provides superior risk management

- **Decision**: Implement correlation-based diversification at strategy level rather than asset level
- **Rationale**: Strategies can be uncorrelated even when trading same assets due to different logic and timing
- **Trade-offs**: More complex correlation calculations vs asset-only correlation, but enables better diversification

- **Decision**: Automated rebalancing with manual override capabilities
- **Rationale**: Reduces emotional decision-making while maintaining user control for market regime changes
- **Trade-offs**: Potential for suboptimal timing vs human judgment, but ensures disciplined execution

- **Decision**: Real-time portfolio monitoring with sub-30 second update latency
- **Rationale**: Enables rapid response to portfolio drift and risk limit breaches
- **Trade-offs**: Higher system resource usage vs delayed updates, but critical for risk management

## 2. Shared Component Architecture

### 2.1 Portfolio Optimization Engine
- **Purpose**: Calculates optimal strategy allocations using Modern Portfolio Theory
- **Used By**: F003-US001 (portfolio construction), F003-US002 (rebalancing decisions)
- **Behaviors**: 
  - Maintains efficient frontier calculations across active strategies
  - Coordinates with PyPortfolioOpt library for mean-variance optimization
  - Validates allocation constraints (max 30% single strategy, min 5% included strategies)
  - Processes correlation matrices from strategy returns data
- **Constraints**: Complete optimization within 30 seconds for 50+ strategies, handle correlation matrix updates without recalculation delays
- **Technology**: PyPortfolioOpt with custom constraint handling, PostgreSQL for historical returns

### 2.2 Strategy Performance Aggregator
- **Purpose**: Consolidates individual strategy performance data for portfolio-level analysis
- **Used By**: F003-US001 (allocation inputs), F003-US003 (risk monitoring)
- **Behaviors**:
  - Tracks real-time P&L from Alpaca API across all active strategies
  - Maintains rolling performance windows (daily, weekly, monthly returns)
  - Calculates strategy-level Sharpe ratios and maximum drawdowns
  - Enables correlation analysis between strategy returns
- **Constraints**: Sub-second latency for real-time updates, handle 50+ concurrent strategy feeds
- **Technology**: Alpaca WebSocket integration, Redis for real-time state, TimescaleDB for historical aggregation

### 2.3 Rebalancing Decision Engine
- **Purpose**: Determines when portfolio rebalancing is required and executes allocation changes
- **Used By**: F003-US002 (automated rotation), F003-US003 (risk-triggered rebalancing)
- **Behaviors**:
  - Monitors allocation drift against target weights (>5% triggers rebalancing)
  - Evaluates strategy performance decay (Sharpe <80% of target)
  - Coordinates strategy retirement after 60+ days underperformance
  - Manages new strategy introduction based on correlation requirements
- **Constraints**: Process rebalancing decisions within 1 minute, maintain audit trail of all allocation changes
- **Technology**: Celery for background processing, PostgreSQL for decision logging

### 2.4 Risk Monitoring System
- **Purpose**: Provides real-time portfolio risk assessment and limit enforcement
- **Used By**: F003-US003 (risk dashboard), F003-US002 (risk-based rotation triggers)
- **Behaviors**:
  - Calculates portfolio Value-at-Risk using historical simulation method
  - Tracks individual strategy drawdowns against predefined limits
  - Monitors aggregate position exposure across correlated strategies
  - Enables real-time risk alerts through notification system
- **Constraints**: Risk calculations update within 30 seconds of market data changes, support configurable risk limits
- **Technology**: Custom VaR calculations with pandas/numpy, SVC-005 for alert delivery

## 3. Data Architecture

### 3.1 Portfolio State Management
Portfolio allocation data persists in PostgreSQL with current weights, target weights, and rebalancing history. Strategy performance aggregations utilize TimescaleDB for efficient time-series queries across multiple strategies. Redis maintains real-time portfolio state including current P&L, active positions, and pending rebalancing decisions.

### 3.2 Strategy Return Correlation Matrix
Historical strategy returns stored in TimescaleDB enable rolling correlation calculations across multiple time windows (30-day, 90-day, 1-year). Correlation matrices cached in Redis for rapid portfolio optimization access. Strategy return data sourced from individual strategy execution results rather than underlying asset prices.

### 3.3 Risk Metrics Storage
Portfolio risk metrics including VaR, drawdown statistics, and exposure limits stored in PostgreSQL with daily snapshots. Real-time risk calculations maintained in Redis for immediate dashboard updates. Historical risk evolution tracked for regime change detection and model validation.

## 4. Service Layer

### 4.1 Portfolio Construction Service
- **Technology**: FastAPI with PyPortfolioOpt integration
- **Responsibility**: Manages optimal allocation calculations using Modern Portfolio Theory
- **Performance**: Complete optimization within 30 seconds for 50+ strategies, handle constraint modifications without full recalculation

### 4.2 Strategy Lifecycle Management Service
- **Technology**: Celery workers with PostgreSQL state management
- **Responsibility**: Coordinates strategy introduction, performance monitoring, and retirement decisions
- **Performance**: Process lifecycle transitions within 1 minute, maintain complete audit trail of strategy status changes

### 4.3 Real-time Portfolio Monitoring Service
- **Technology**: WebSocket connections with Alpaca API integration
- **Responsibility**: Provides continuous portfolio state updates and risk monitoring
- **Performance**: Sub-30 second latency for portfolio updates, handle 50+ concurrent strategy feeds without degradation

### 4.4 Risk Management Service
- **Technology**: Custom risk calculations with pandas/numpy, Redis caching
- **Responsibility**: Maintains portfolio risk metrics and enforces risk limits
- **Performance**: Risk calculations complete within 30 seconds, support real-time limit monitoring

## 5. Integration Architecture

### 5.1 Strategy Execution Engine Integration
F003 integrates with SVC-002 (strategy execution engine) to access individual strategy performance data, execution status, and position information. This integration enables portfolio-level aggregation of strategy returns for correlation analysis and risk monitoring.

### 5.2 Market Data Pipeline Integration
Portfolio monitoring requires real-time market data from SVC-001 for mark-to-market calculations and risk assessment. Integration handles multiple asset classes (equities, FX, futures) with proper timezone coordination.

### 5.3 Notification System Integration
Risk alerts, rebalancing notifications, and portfolio status updates flow through SVC-005 (real-time notifications) to provide immediate user feedback on portfolio changes and risk limit breaches.

### 5.4 Validation Framework Integration
New strategy introduction requires validation through SVC-003 to ensure strategies meet correlation and performance requirements before portfolio inclusion.

## 6. Architecture Validation

| Story | Components | Services | Requirements |
|-------|-----------|----------|--------------|
| F003-US001 | Portfolio Optimization Engine, Strategy Performance Aggregator | Portfolio Construction Service, Strategy Execution Engine (SVC-002) | FR-009: MPT-based construction with allocation constraints |
| F003-US002 | Rebalancing Decision Engine, Strategy Performance Aggregator | Strategy Lifecycle Management Service, Async Task Processor (SVC-004) | FR-010: Automated rotation based on performance decay |
| F003-US003 | Risk Monitoring System, Portfolio Optimization Engine | Real-time Portfolio Monitoring Service, Real-time Notifications (SVC-005) | FR-011: Comprehensive risk dashboard with real-time updates |

### 6.1 Cross-Story Validation
- **Shared Data Flow**: Strategy performance data flows from SVC-002 through Strategy Performance Aggregator to all portfolio management components
- **Consistent Risk Framework**: Risk Monitoring System provides unified risk assessment across construction, rebalancing, and monitoring functions
- **Real-time Coordination**: All components utilize Redis for consistent real-time state management and WebSocket updates through SVC-005

### 6.2 Performance Validation
- Portfolio optimization completes within 30-second requirement using PyPortfolioOpt efficient algorithms
- Real-time monitoring achieves sub-30 second update latency through Redis caching and WebSocket architecture
- Strategy correlation calculations leverage TimescaleDB time-series optimizations for rapid matrix updates

### 6.3 Integration Validation
- PostgreSQL with TimescaleDB provides required time-series performance for historical strategy returns
- Redis enables real-time portfolio state management across all components
- Celery background processing handles computationally intensive optimization tasks without blocking user interface
- Alpaca API integration provides real-time position and P&L data for accurate portfolio monitoring