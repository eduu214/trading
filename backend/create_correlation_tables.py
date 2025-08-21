"""
Create correlation tables in database
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.models.strategy_correlation import Base

async def create_tables():
    """Create correlation tables"""
    
    async with engine.begin() as conn:
        # Create schema if it doesn't exist
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS trading"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Correlation tables created successfully")
        
        # Note: TimescaleDB setup would be run separately if TimescaleDB is installed
        print("ℹ️  TimescaleDB setup skipped (run manually if TimescaleDB is installed)")

if __name__ == "__main__":
    asyncio.run(create_tables())