# Feature Technical Architecture - F003: Strategy Portfolio Management

## 1. Architecture Overview

### 1.1 Technical Strategy
F003 leverages PostgreSQL with TimescaleDB for time-series portfolio data, Redis for real-time correlation caching, and FastAPI with Celery for portfolio optimization processing. The architecture centers on PyPortfolioOpt for modern portfolio theory calculations while maintaining real-time synchronization with Alpaca's portfolio API for live position tracking.

### 1.2 Key Decisions
- **Decision**: Use PyPortfolioOpt for portfolio optimization over custom algorithms
- **Rationale**: Proven implementation of modern portfolio theory with efficient frontier calculations, extensive backtesting in academic literature
- **Trade-offs**: Gain mathematical rigor and performance, sacrifice custom optimization flexibility

- **Decision**: Cache correlation matrices in Redis with 15-minute refresh cycles
- **Rationale**: Correlation calculations are computationally expensive but don't require second-by-second updates for portfolio decisions
- **Trade-offs**: Gain sub-second portfolio queries, sacrifice real-time correlation precision

- **Decision**: Implement strategy lifecycle as finite state machine in PostgreSQL
- **Rationale**: Clear state transitions prevent invalid operations and provide audit trail for regulatory compliance
- **Trade-offs**: Gain operational safety and compliance, sacrifice implementation simplicity

## 2. Shared Component Architecture

### 2.1 Portfolio Optimization Engine
- **Purpose**: Calculates optimal strategy allocations using modern portfolio theory
- **Used By**: F003-US001 (portfolio construction), F003-US002 (rebalancing decisions)
- **Behaviors**: 
  - Maintains correlation matrices for all active strategies
  - Coordinates with PyPortfolioOpt for efficient frontier calculations
  - Validates allocation constraints against account buying power
  - Enables risk-adjusted return optimization with customizable objectives
- **Constraints**: Complete optimization within 30 seconds for 50+ strategy portfolio
- **Technology**: PyPortfolioOpt + NumPy for mathematical operations

### 2.2 Strategy Lifecycle Manager
- **Purpose**: Tracks and manages strategy states from discovery through retirement
- **Used By**: F003-US002 (rotation decisions), F003-US003 (risk monitoring)
- **Behaviors**:
  - Maintains finite state machine for strategy lifecycle (Discovery → Validation → Paper → Live → Retired)
  - Coordinates state transitions with validation requirements
  - Tracks performance metrics and triggers for each lifecycle stage
  - Enables automated retirement based on performance thresholds
- **Constraints**: State transitions must be atomic and logged for audit compliance
- **Technology**: PostgreSQL with custom state machine implementation

### 2.3 Real-Time Position Tracker
- **Purpose**: Synchronizes portfolio state with live broker positions
- **Used By**: F003-US001 (current allocations), F003-US003 (risk calculations)
- **Behaviors**:
  - Maintains real-time synchronization with Alpaca portfolio API
  - Tracks position changes and cash flows across all strategies
  - Validates position consistency between internal state and broker
  - Enables fractional share position management
- **Constraints**: Position updates within 30 seconds of broker changes
- **Technology**: Alpaca WebSocket API + Redis for position caching

### 2.4 Correlation Analysis Service
- **Purpose**: Calculates and monitors strategy correlations for diversification
- **Used By**: F003-US001 (allocation decisions), F003-US002 (rotation triggers)
- **Behaviors**:
  - Maintains rolling correlation matrices across multiple timeframes
  - Monitors correlation regime changes and threshold breaches
  - Calculates portfolio-level correlation metrics and diversification ratios
  - Enables correlation-based strategy filtering and selection
- **Constraints**: Update correlations every 15 minutes during market hours
- **Technology**: Pandas/NumPy for correlation calculations + Redis caching

## 3. Data Architecture

### 3.1 Portfolio State Management
Portfolio data persists in PostgreSQL with TimescaleDB optimization for time-series performance tracking. Core entities include Strategy (parameters and metadata), Position (current allocations), and PerformanceHistory (time-series returns). Strategy-to-Position relationships support many-to-many allocation tracking, while PerformanceHistory enables correlation analysis across multiple timeframes.

### 3.2 Strategy Lifecycle Data
Strategy lifecycle states persist as enumerated values with transition timestamps and triggering conditions. Each state change creates immutable audit records for regulatory compliance. Performance thresholds and rotation rules store as JSON configurations enabling flexible strategy management without schema changes.

### 3.3 Correlation Data Structures
Correlation matrices store as compressed arrays in Redis with timestamp metadata for cache invalidation. Historical correlation data persists in PostgreSQL TimescaleDB for regime analysis and backtesting. Portfolio-level correlation metrics calculate on-demand from cached strategy correlations.

## 4. Service Layer

### 4.1 Portfolio Construction Service
- **Technology**: FastAPI + PyPortfolioOpt + PostgreSQL
- **Responsibility**: Manages optimal allocation calculations and constraint validation
- **Performance**: Complete 50-strategy optimization within 30 seconds using efficient frontier algorithms

### 4.2 Strategy Rotation Service  
- **Technology**: Celery + PostgreSQL + Redis
- **Responsibility**: Monitors strategy performance and executes automated rotation decisions
- **Performance**: Process rotation decisions within 5 minutes of trigger conditions

### 4.3 Risk Management Service
- **Technology**: FastAPI + NumPy + Alpaca API
- **Responsibility**: Calculates portfolio risk metrics and enforces position limits
- **Performance**: Real-time risk calculations with sub-second response for dashboard updates

### 4.4 Rebalancing Execution Service
- **Technology**: Alpaca SDK + PostgreSQL + Redis
- **Responsibility**: Executes portfolio rebalancing through fractional share orders
- **Performance**: Complete rebalancing execution within 2 minutes of approval

## 5. Integration Architecture

### 5.1 Market Data Integration
Integrates with SVC-001 (market_data_pipeline) for strategy performance data and correlation inputs. Receives real-time price updates for portfolio valuation and risk calculations. Handles market hours coordination for rebalancing timing.

### 5.2 Strategy Execution Integration
Coordinates with SVC-002 (strategy_execution_engine) for individual strategy performance tracking and position updates. Receives strategy signals for portfolio impact analysis and correlation monitoring.

### 5.3 Validation Framework Integration
Integrates with SVC-003 (validation_framework) for strategy lifecycle transitions. Validates portfolio constraints and risk limits before rebalancing execution. Coordinates paper trading requirements for new strategy deployment.

### 5.4 Notification Integration
Uses SVC-005 (real_time_notifications) for portfolio change alerts and rebalancing notifications. Sends correlation threshold breach alerts and strategy rotation notifications to dashboard.

### 5.5 External Broker Integration
Direct integration with EXT-002 (alpaca_trading_api) for position synchronization and rebalancing execution. Maintains separate paper and live trading contexts with identical portfolio logic.

## 6. Architecture Validation

| Story | Components | Services | Requirements |
|-------|-----------|----------|--------------|
| F003-US001 | Portfolio Optimization Engine, Correlation Analysis Service, Real-Time Position Tracker | Portfolio Construction Service, Risk Management Service | FR-009: Correlation-based construction with 50% max allocation and 5-strategy minimum |
| F003-US002 | Strategy Lifecycle Manager, Portfolio Optimization Engine | Strategy Rotation Service, Rebalancing Execution Service | FR-010: Automated rotation with 60-day underperformance threshold |
| F003-US003 | Real-Time Position Tracker, Correlation Analysis Service | Risk Management Service | FR-011: Real-time VaR calculation and drawdown monitoring |

### 6.1 Performance Validation
- Portfolio optimization completes within 30 seconds for 50+ strategies using PyPortfolioOpt's efficient algorithms
- Correlation updates every 15 minutes provide sufficient precision for portfolio decisions while maintaining performance
- Real-time position tracking synchronizes with Alpaca within 30 seconds of broker changes

### 6.2 Scalability Validation  
- PostgreSQL with TimescaleDB handles time-series performance data for 100+ strategies
- Redis correlation caching supports sub-second portfolio queries at scale
- Celery task processing enables parallel strategy analysis and rotation decisions

### 6.3 Integration Validation
- All shared services from infrastructure registry properly integrated with defined interfaces
- External API integration follows rate limits and error handling patterns
- Cross-feature coordination maintains data consistency and audit trails