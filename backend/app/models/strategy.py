from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Enum, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class StrategyStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    BACKTESTING = "backtesting"
    PAPER_TRADING = "paper_trading"
    LIVE = "live"
    PAUSED = "paused"
    RETIRED = "retired"


class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"))
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(String(100), nullable=False)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.DISCOVERED)
    
    # Performance metrics
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    
    # Risk parameters
    position_size = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    max_positions = Column(Integer, default=1)
    
    # Configuration
    parameters = Column(JSON)
    entry_rules = Column(JSON)
    exit_rules = Column(JSON)
    
    # Code generation
    generated_code = Column(JSON)  # Stores code for different platforms
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime)
    deactivated_at = Column(DateTime)
    
    # Flags
    is_active = Column(Boolean, default=False)
    auto_trade = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Strategy {self.name} - {self.status}>"