from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter()


class PortfolioResponse(BaseModel):
    total_value: float
    daily_pnl: float
    total_pnl: float
    strategy_count: int


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    """Get portfolio overview"""
    return {
        "total_value": 0.0,
        "daily_pnl": 0.0,
        "total_pnl": 0.0,
        "strategy_count": 0
    }