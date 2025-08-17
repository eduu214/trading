-- Add complexity fields to strategies table
ALTER TABLE strategies 
ADD COLUMN IF NOT EXISTS complexity_level INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS complexity_score FLOAT,
ADD COLUMN IF NOT EXISTS optimal_complexity INTEGER,
ADD COLUMN IF NOT EXISTS last_optimized TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS optimization_metrics JSONB;

-- Create index for faster complexity queries
CREATE INDEX IF NOT EXISTS ix_strategies_complexity_level 
ON strategies(complexity_level);

-- Create complexity_history table for tracking optimization history
CREATE TABLE IF NOT EXISTS complexity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    complexity_level INTEGER NOT NULL,
    score FLOAT NOT NULL,
    sharpe_ratio FLOAT,
    max_drawdown FLOAT,
    risk_adjusted_return FLOAT,
    confidence FLOAT,
    recommendation TEXT,
    metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    risk_preference VARCHAR(50)
);

-- Create index on strategy_id for faster lookups
CREATE INDEX IF NOT EXISTS ix_complexity_history_strategy_id 
ON complexity_history(strategy_id);