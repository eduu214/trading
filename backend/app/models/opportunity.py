from sqlalchemy import Column, String, Float, DateTime, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class AssetClass(str, enum.Enum):
    EQUITIES = "equities"
    FUTURES = "futures"
    FX = "fx"
    CRYPTO = "crypto"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_class = Column(Enum(AssetClass), nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy_type = Column(String(100), nullable=False)
    opportunity_score = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    correlation_to_portfolio = Column(Float, default=0.0)
    
    # Additional metadata
    entry_conditions = Column(JSON)
    exit_conditions = Column(JSON)
    technical_indicators = Column(JSON)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Analysis details
    backtest_results = Column(JSON)
    market_conditions = Column(JSON)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Opportunity {self.symbol} - {self.strategy_type} - Score: {self.opportunity_score}>"