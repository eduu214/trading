"""
Strategy Correlation Data Model
F001-US003 Task 1: PostgreSQL schema for correlation matrices with TimescaleDB

Handles:
- Strategy correlation matrix storage
- Historical correlation tracking
- Diversification score calculations
- Sub-second query performance for 50+ strategies
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Index, UniqueConstraint, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, List, Optional

Base = declarative_base()


class StrategyCorrelation(Base):
    """Strategy correlation matrix data"""
    __tablename__ = 'strategy_correlations'
    
    id = Column(Integer, primary_key=True)
    strategy_id_1 = Column(String(100), nullable=False, index=True)
    strategy_id_2 = Column(String(100), nullable=False, index=True)
    correlation_coefficient = Column(Float, nullable=False)
    
    # Time-based fields for TimescaleDB partitioning
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    time_period = Column(String(50), nullable=False, default='30d')  # 30d, 60d, 90d, 1y
    
    # Metadata
    sample_size = Column(Integer, nullable=False)  # Number of data points used
    confidence_level = Column(Float, nullable=False, default=0.95)
    calculation_method = Column(String(50), nullable=False, default='pearson')
    
    # Performance tracking
    strategy_1_return = Column(Float)  # Avg return for period
    strategy_2_return = Column(Float)
    strategy_1_volatility = Column(Float)
    strategy_2_volatility = Column(Float)
    
    __table_args__ = (
        # Unique constraint to prevent duplicate correlations
        UniqueConstraint('strategy_id_1', 'strategy_id_2', 'time_period', 'calculated_at', 
                        name='unique_strategy_correlation'),
        # Composite index for fast queries
        Index('idx_correlation_lookup', 'strategy_id_1', 'strategy_id_2', 'calculated_at'),
        Index('idx_correlation_time', 'calculated_at', 'time_period'),
        {'schema': 'trading'}
    )


class CorrelationMatrix(Base):
    """Full correlation matrix snapshot for efficient retrieval"""
    __tablename__ = 'correlation_matrices'
    
    id = Column(Integer, primary_key=True)
    matrix_id = Column(String(100), unique=True, nullable=False)
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Store entire matrix as JSON for fast retrieval
    matrix_data = Column(JSON, nullable=False)
    # Example structure:
    # {
    #   "strategies": ["strat1", "strat2", "strat3"],
    #   "matrix": [[1.0, 0.3, 0.5], [0.3, 1.0, 0.2], [0.5, 0.2, 1.0]],
    #   "metadata": {"time_period": "30d", "sample_size": 252}
    # }
    
    # Metadata
    num_strategies = Column(Integer, nullable=False)
    time_period = Column(String(50), nullable=False, default='30d')
    avg_correlation = Column(Float)  # Average pairwise correlation
    max_correlation = Column(Float)  # Highest correlation (excluding diagonal)
    min_correlation = Column(Float)  # Lowest correlation
    
    # Cache control
    cache_ttl = Column(Integer, default=900)  # 15 minutes default
    is_current = Column(String(1), default='Y')  # Mark current vs historical
    
    __table_args__ = (
        Index('idx_matrix_current', 'is_current', 'calculated_at'),
        Index('idx_matrix_lookup', 'matrix_id', 'calculated_at'),
        {'schema': 'trading'}
    )


class DiversificationScore(Base):
    """Portfolio diversification scores based on correlation analysis"""
    __tablename__ = 'diversification_scores'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(String(100), nullable=False, index=True)
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Diversification metrics (0-100 scale)
    overall_score = Column(Float, nullable=False)  # Main diversification score
    correlation_score = Column(Float, nullable=False)  # Based on avg correlation
    asset_class_score = Column(Float)  # Diversity across asset classes
    strategy_type_score = Column(Float)  # Diversity across strategy types
    timeframe_score = Column(Float)  # Diversity across holding periods
    
    # Portfolio composition
    num_strategies = Column(Integer, nullable=False)
    strategy_weights = Column(JSON)  # {"strat1": 0.3, "strat2": 0.4, ...}
    
    # Correlation statistics
    avg_correlation = Column(Float, nullable=False)
    max_correlation = Column(Float)
    correlation_above_threshold = Column(Integer, default=0)  # Count > 0.6
    
    # Risk metrics
    portfolio_volatility = Column(Float)
    concentration_risk = Column(Float)  # Herfindahl index
    
    __table_args__ = (
        Index('idx_diversification_portfolio', 'portfolio_id', 'calculated_at'),
        Index('idx_diversification_current', 'portfolio_id', 'calculated_at'),
        {'schema': 'trading'}
    )


class StrategyCluster(Base):
    """Strategy clustering based on correlation patterns"""
    __tablename__ = 'strategy_clusters'
    
    id = Column(Integer, primary_key=True)
    cluster_id = Column(String(100), nullable=False, index=True)
    cluster_name = Column(String(200))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Cluster characteristics
    num_strategies = Column(Integer, nullable=False)
    strategy_list = Column(JSON, nullable=False)  # List of strategy IDs
    avg_intra_correlation = Column(Float)  # Avg correlation within cluster
    avg_inter_correlation = Column(Float)  # Avg correlation with other clusters
    
    # Cluster metadata
    cluster_type = Column(String(50))  # momentum, mean_reversion, arbitrage, etc
    dominant_asset_class = Column(String(50))  # equities, futures, fx
    avg_holding_period = Column(String(50))  # intraday, daily, weekly, monthly
    
    __table_args__ = (
        Index('idx_cluster_lookup', 'cluster_id', 'created_at'),
        {'schema': 'trading'}
    )


class CorrelationAlert(Base):
    """Alerts for high correlation warnings"""
    __tablename__ = 'correlation_alerts'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # high_correlation, cluster_risk, etc
    severity = Column(String(20), nullable=False)  # warning, critical
    
    # Affected strategies
    strategy_id_1 = Column(String(100), nullable=False)
    strategy_id_2 = Column(String(100), nullable=False)
    correlation_value = Column(Float, nullable=False)
    
    # Alert status
    is_active = Column(String(1), default='Y')
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    resolution_notes = Column(Text)
    
    __table_args__ = (
        Index('idx_alert_active', 'is_active', 'created_at'),
        Index('idx_alert_strategies', 'strategy_id_1', 'strategy_id_2'),
        {'schema': 'trading'}
    )


# TimescaleDB hypertable creation SQL (run after table creation)
TIMESCALE_SETUP = """
-- Convert strategy_correlations to hypertable for time-series optimization
SELECT create_hypertable('trading.strategy_correlations', 'calculated_at', 
                         chunk_time_interval => INTERVAL '7 days',
                         if_not_exists => TRUE);

-- Add compression policy for older data
ALTER TABLE trading.strategy_correlations SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'strategy_id_1,strategy_id_2,time_period'
);

SELECT add_compression_policy('trading.strategy_correlations', 
                              INTERVAL '30 days',
                              if_not_exists => TRUE);

-- Convert diversification_scores to hypertable
SELECT create_hypertable('trading.diversification_scores', 'calculated_at',
                         chunk_time_interval => INTERVAL '7 days',
                         if_not_exists => TRUE);

-- Create continuous aggregate for latest correlations
CREATE MATERIALIZED VIEW trading.latest_correlations
WITH (timescaledb.continuous) AS
SELECT 
    strategy_id_1,
    strategy_id_2,
    time_period,
    last(correlation_coefficient, calculated_at) as correlation,
    last(calculated_at, calculated_at) as last_calculated,
    last(sample_size, calculated_at) as sample_size
FROM trading.strategy_correlations
WHERE calculated_at > NOW() - INTERVAL '7 days'
GROUP BY strategy_id_1, strategy_id_2, time_period
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('trading.latest_correlations',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE);
"""