-- Add complexity constraint tables for F001-US002 Slice 2

-- Create complexity_constraints table
CREATE TABLE IF NOT EXISTS complexity_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL,
    operator VARCHAR(10) NOT NULL,
    value FLOAT NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1D',
    is_active BOOLEAN DEFAULT true,
    is_hard_constraint BOOLEAN DEFAULT false,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create complexity_presets table
CREATE TABLE IF NOT EXISTS complexity_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    risk_preference VARCHAR(50) DEFAULT 'balanced',
    constraints JSONB,
    default_timeframe VARCHAR(10) DEFAULT '1D',
    times_used INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    is_system BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create multi_timeframe_analysis table
CREATE TABLE IF NOT EXISTS multi_timeframe_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    primary_timeframe VARCHAR(10) NOT NULL,
    secondary_timeframes JSONB,
    results JSONB,
    weighted_complexity FLOAT,
    optimal_complexity INTEGER,
    confidence_score FLOAT,
    timeframe_correlation JSONB,
    consistency_score FLOAT,
    analysis_duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_complexity_constraints_strategy_id ON complexity_constraints(strategy_id);
CREATE INDEX idx_complexity_constraints_active ON complexity_constraints(is_active);
CREATE INDEX idx_multi_timeframe_strategy_id ON multi_timeframe_analysis(strategy_id);
CREATE INDEX idx_complexity_presets_system ON complexity_presets(is_system);

-- Insert system presets
INSERT INTO complexity_presets (name, description, risk_preference, constraints, is_system, is_default)
VALUES 
    ('Conservative', 'Low risk, stable returns', 'conservative', 
     '[{"type": "MAX_DRAWDOWN", "operator": ">=", "value": -10, "is_hard": true},
       {"type": "MAX_VOLATILITY", "operator": "<=", "value": 15, "weight": 0.8},
       {"type": "MIN_SHARPE", "operator": ">=", "value": 1.0, "weight": 1}]'::jsonb,
     true, false),
    
    ('Balanced', 'Moderate risk and return', 'balanced',
     '[{"type": "MAX_DRAWDOWN", "operator": ">=", "value": -15, "is_hard": true},
       {"type": "MIN_SHARPE", "operator": ">=", "value": 1.2, "weight": 1}]'::jsonb,
     true, true),
    
    ('Aggressive', 'Higher risk for maximum returns', 'aggressive',
     '[{"type": "MAX_DRAWDOWN", "operator": ">=", "value": -25, "weight": 0.5},
       {"type": "MIN_SHARPE", "operator": ">=", "value": 1.5, "is_hard": true},
       {"type": "TARGET_RETURN", "operator": ">=", "value": 20, "weight": 0.7}]'::jsonb,
     true, false);
