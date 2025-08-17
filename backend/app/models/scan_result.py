from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(100), nullable=False)
    
    # Scan configuration
    asset_classes = Column(JSON)
    correlation_threshold = Column(Float)
    min_opportunity_score = Column(Float)
    
    # Results
    opportunities_found = Column(Integer, default=0)
    symbols_scanned = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Metadata
    scan_metadata = Column(JSON)
    error_log = Column(JSON)
    
    def __repr__(self):
        return f"<ScanResult {self.scan_id} - {self.opportunities_found} opportunities>"