"""
Models for complexity constraints and presets
Part of F001-US002 Slice 2 implementation
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class ConstraintType(str, enum.Enum):
    """Types of complexity constraints"""
    MIN_SHARPE = "min_sharpe"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_VOLATILITY = "max_volatility"
    MIN_WIN_RATE = "min_win_rate"
    MIN_PROFIT_FACTOR = "min_profit_factor"
    MAX_COMPLEXITY = "max_complexity"
    MIN_COMPLEXITY = "min_complexity"
    TARGET_RETURN = "target_return"
    RISK_LIMIT = "risk_limit"


class TimeframeType(str, enum.Enum):
    """Supported analysis timeframes"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    HOUR_4 = "4H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"


class ComplexityConstraint(Base):
    """Individual complexity constraint"""
    __tablename__ = "complexity_constraints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"))
    
    # Constraint definition
    constraint_type = Column(Enum(ConstraintType), nullable=False)
    operator = Column(String(10), nullable=False)  # >, <, >=, <=, ==
    value = Column(Float, nullable=False)
    
    # Configuration
    timeframe = Column(Enum(TimeframeType), default=TimeframeType.DAY_1)
    is_active = Column(Boolean, default=True)
    is_hard_constraint = Column(Boolean, default=False)  # If true, must be satisfied
    weight = Column(Float, default=1.0)  # Importance weight for soft constraints
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="constraints")
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if constraint is satisfied"""
        if self.operator == ">":
            return value > self.value
        elif self.operator == "<":
            return value < self.value
        elif self.operator == ">=":
            return value >= self.value
        elif self.operator == "<=":
            return value <= self.value
        elif self.operator == "==":
            return abs(value - self.value) < 0.0001
        return False
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "strategy_id": str(self.strategy_id),
            "constraint_type": self.constraint_type.value,
            "operator": self.operator,
            "value": self.value,
            "timeframe": self.timeframe.value,
            "is_active": self.is_active,
            "is_hard_constraint": self.is_hard_constraint,
            "weight": self.weight
        }


class ComplexityPreset(Base):
    """Predefined complexity constraint presets"""
    __tablename__ = "complexity_presets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    
    # Preset configuration
    risk_preference = Column(String(50), default="balanced")  # conservative, balanced, aggressive
    constraints = Column(JSON)  # List of constraint definitions
    default_timeframe = Column(Enum(TimeframeType), default=TimeframeType.DAY_1)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # System presets
    is_system = Column(Boolean, default=False)  # Cannot be modified by users
    is_default = Column(Boolean, default=False)  # Default preset for new strategies
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "risk_preference": self.risk_preference,
            "constraints": self.constraints,
            "default_timeframe": self.default_timeframe.value if self.default_timeframe else None,
            "times_used": self.times_used,
            "is_system": self.is_system,
            "is_default": self.is_default
        }


class MultiTimeframeAnalysis(Base):
    """Results of multi-timeframe complexity analysis"""
    __tablename__ = "multi_timeframe_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"))
    
    # Analysis parameters
    primary_timeframe = Column(Enum(TimeframeType), nullable=False)
    secondary_timeframes = Column(JSON)  # List of additional timeframes
    
    # Results per timeframe
    results = Column(JSON)  # Dict mapping timeframe -> complexity scores
    
    # Aggregated results
    weighted_complexity = Column(Float)  # Weighted average across timeframes
    optimal_complexity = Column(Integer)  # Recommended level considering all timeframes
    confidence_score = Column(Float)  # Confidence in recommendation
    
    # Correlation analysis
    timeframe_correlation = Column(JSON)  # Correlation matrix between timeframes
    consistency_score = Column(Float)  # How consistent are results across timeframes
    
    # Metadata
    analysis_duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="multi_timeframe_analyses")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "strategy_id": str(self.strategy_id),
            "primary_timeframe": self.primary_timeframe.value,
            "secondary_timeframes": self.secondary_timeframes,
            "results": self.results,
            "weighted_complexity": self.weighted_complexity,
            "optimal_complexity": self.optimal_complexity,
            "confidence_score": self.confidence_score,
            "timeframe_correlation": self.timeframe_correlation,
            "consistency_score": self.consistency_score,
            "analysis_duration_seconds": self.analysis_duration_seconds
        }