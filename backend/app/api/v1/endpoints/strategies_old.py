from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter()


class StrategyResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    performance: float


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(db: AsyncSession = Depends(get_db)):
    """Get all strategies"""
    return []


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str, db: AsyncSession = Depends(get_db)):
    """Get specific strategy details"""
    return {
        "id": strategy_id,
        "name": "Sample Strategy",
        "type": "momentum",
        "status": "active",
        "performance": 0.0
    }