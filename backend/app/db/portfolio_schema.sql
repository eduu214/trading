-- F003-US001 Portfolio Management Database Schema
-- PostgreSQL 16 with TimescaleDB extension
-- Created for AlphaStrat Portfolio Management Feature

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Portfolio Allocations Table
-- Stores current weights, target weights, and rebalancing history
CREATE TABLE IF NOT EXISTS portfolio_allocations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Portfolio identification
    portfolio_id VARCHAR(50) NOT NULL DEFAULT 'main',
    strategy_id VARCHAR(100) NOT NULL,
    
    -- Allocation data
    current_weight DECIMAL(8,6) NOT NULL CHECK (current_weight >= 0 AND current_weight <= 1),
    target_weight DECIMAL(8,6) NOT NULL CHECK (target_weight >= 0 AND target_weight <= 1),
    previous_weight DECIMAL(8,6),
    
    -- Rebalancing metadata
    last_rebalanced_at TIMESTAMPTZ,
    rebalance_reason VARCHAR(200),
    drift_percentage DECIMAL(8,4),
    
    -- Constraints and limits
    max_allocation DECIMAL(8,6) DEFAULT 0.30 CHECK (max_allocation <= 1),
    min_allocation DECIMAL(8,6) DEFAULT 0.05 CHECK (min_allocation >= 0),
    
    -- Status tracking
    is_active BOOLEAN DEFAULT true,
    allocation_status VARCHAR(20) DEFAULT 'active' CHECK (allocation_status IN ('active', 'paused', 'retiring', 'retired')),
    
    UNIQUE(portfolio_id, strategy_id, created_at)
);

-- Create hypertable for portfolio allocations
SELECT create_hypertable('portfolio_allocations', 'created_at', if_not_exists => TRUE);

-- Strategy Performance Table
-- Performance aggregations using TimescaleDB for time-series queries
CREATE TABLE IF NOT EXISTS strategy_performance (
    time TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(100) NOT NULL,
    
    -- Daily performance metrics
    daily_return DECIMAL(10,6),
    cumulative_return DECIMAL(10,6),
    daily_pnl DECIMAL(15,2),
    cumulative_pnl DECIMAL(15,2),
    
    -- Risk metrics
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    volatility DECIMAL(8,4),
    
    -- Rolling window metrics (30-day, 90-day, 1-year)
    sharpe_30d DECIMAL(8,4),
    sharpe_90d DECIMAL(8,4),
    sharpe_1y DECIMAL(8,4),
    return_30d DECIMAL(10,6),
    return_90d DECIMAL(10,6),
    return_1y DECIMAL(10,6),
    
    -- Position data
    market_value DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    realized_pnl DECIMAL(15,2),
    
    -- Performance degradation tracking
    performance_decay_score DECIMAL(6,4),
    underperformance_days INTEGER DEFAULT 0,
    
    PRIMARY KEY (time, strategy_id)
);

-- Create hypertable for strategy performance
SELECT create_hypertable('strategy_performance', 'time', if_not_exists => TRUE);

-- Correlation Matrices Table
-- Strategy return correlation data for portfolio optimization
CREATE TABLE IF NOT EXISTS correlation_matrices (
    id SERIAL PRIMARY KEY,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Time window for correlation calculation
    window_days INTEGER NOT NULL CHECK (window_days > 0),
    window_type VARCHAR(10) NOT NULL CHECK (window_type IN ('30d', '90d', '1y')),
    
    -- Strategy pair correlation
    strategy_a VARCHAR(100) NOT NULL,
    strategy_b VARCHAR(100) NOT NULL,
    correlation_coefficient DECIMAL(8,6) NOT NULL CHECK (correlation_coefficient >= -1 AND correlation_coefficient <= 1),
    
    -- Statistical significance
    p_value DECIMAL(8,6),
    confidence_level DECIMAL(4,2) DEFAULT 0.95,
    sample_size INTEGER,
    
    -- Quality metrics
    data_quality_score DECIMAL(4,3),
    missing_data_percentage DECIMAL(5,2),
    
    UNIQUE(strategy_a, strategy_b, window_type, calculated_at)
);

-- Create index for correlation lookups
CREATE INDEX IF NOT EXISTS idx_correlation_matrices_strategies 
    ON correlation_matrices(strategy_a, strategy_b, window_type);
CREATE INDEX IF NOT EXISTS idx_correlation_matrices_calculated_at 
    ON correlation_matrices(calculated_at);

-- Portfolio Risk Metrics Table
-- Portfolio-level risk metrics with daily snapshots
CREATE TABLE IF NOT EXISTS portfolio_risk_metrics (
    time TIMESTAMPTZ NOT NULL,
    portfolio_id VARCHAR(50) NOT NULL DEFAULT 'main',
    
    -- Value at Risk calculations
    var_1d_95 DECIMAL(15,2), -- 1-day VaR at 95% confidence
    var_1d_99 DECIMAL(15,2), -- 1-day VaR at 99% confidence
    var_5d_95 DECIMAL(15,2), -- 5-day VaR at 95% confidence
    
    -- Portfolio-level risk metrics
    portfolio_volatility DECIMAL(8,4),
    portfolio_sharpe DECIMAL(8,4),
    portfolio_max_drawdown DECIMAL(8,4),
    portfolio_beta DECIMAL(8,4),
    
    -- Diversification metrics
    concentration_risk DECIMAL(8,4), -- Herfindahl index
    correlation_risk DECIMAL(8,4),   -- Average correlation
    strategy_count INTEGER,
    active_strategy_count INTEGER,
    
    -- Exposure limits
    max_single_strategy_exposure DECIMAL(8,4),
    total_long_exposure DECIMAL(8,4),
    total_short_exposure DECIMAL(8,4),
    net_exposure DECIMAL(8,4),
    
    PRIMARY KEY (time, portfolio_id)
);

-- Create hypertable for portfolio risk metrics
SELECT create_hypertable('portfolio_risk_metrics', 'time', if_not_exists => TRUE);

-- Rebalancing History Table
-- Audit trail of all allocation changes
CREATE TABLE IF NOT EXISTS rebalancing_history (
    id SERIAL PRIMARY KEY,
    rebalanced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    portfolio_id VARCHAR(50) NOT NULL DEFAULT 'main',
    
    -- Rebalancing trigger
    trigger_type VARCHAR(30) NOT NULL CHECK (trigger_type IN (
        'drift_threshold', 'performance_decay', 'risk_limit', 'scheduled', 'manual'
    )),
    trigger_details JSONB,
    
    -- Before/after state
    allocations_before JSONB NOT NULL,
    allocations_after JSONB NOT NULL,
    
    -- Execution details
    execution_time_ms INTEGER,
    strategies_added TEXT[],
    strategies_removed TEXT[],
    strategies_modified TEXT[],
    
    -- Performance impact
    expected_return_change DECIMAL(8,6),
    expected_risk_change DECIMAL(8,6),
    transaction_costs DECIMAL(10,2),
    
    -- Approval and validation
    approved_by VARCHAR(100),
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'failed')),
    validation_errors TEXT[]
);

-- Create indexes for rebalancing history
CREATE INDEX IF NOT EXISTS idx_rebalancing_history_portfolio_time 
    ON rebalancing_history(portfolio_id, rebalanced_at);
CREATE INDEX IF NOT EXISTS idx_rebalancing_history_trigger 
    ON rebalancing_history(trigger_type, rebalanced_at);

-- Add updated_at triggers for portfolio_allocations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_portfolio_allocations_updated_at 
    BEFORE UPDATE ON portfolio_allocations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- Current Portfolio Allocation View
CREATE OR REPLACE VIEW current_portfolio_allocation AS
SELECT DISTINCT ON (strategy_id)
    strategy_id,
    current_weight,
    target_weight,
    drift_percentage,
    allocation_status,
    last_rebalanced_at,
    updated_at
FROM portfolio_allocations 
WHERE is_active = true
ORDER BY strategy_id, created_at DESC;

-- Latest Strategy Performance View
CREATE OR REPLACE VIEW latest_strategy_performance AS
SELECT DISTINCT ON (strategy_id)
    strategy_id,
    time,
    daily_return,
    cumulative_return,
    sharpe_ratio,
    max_drawdown,
    sharpe_30d,
    return_30d,
    market_value,
    unrealized_pnl,
    performance_decay_score,
    underperformance_days
FROM strategy_performance
ORDER BY strategy_id, time DESC;

-- Portfolio Risk Dashboard View
CREATE OR REPLACE VIEW portfolio_risk_dashboard AS
SELECT 
    prm.*,
    cpa.total_strategies,
    cpa.total_allocation
FROM (
    SELECT DISTINCT ON (portfolio_id)
        *
    FROM portfolio_risk_metrics
    ORDER BY portfolio_id, time DESC
) prm
LEFT JOIN (
    SELECT 
        'main' as portfolio_id,
        COUNT(*) as total_strategies,
        SUM(current_weight) as total_allocation
    FROM current_portfolio_allocation
    WHERE allocation_status = 'active'
) cpa ON prm.portfolio_id = cpa.portfolio_id;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_app;