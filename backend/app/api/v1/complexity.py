"""
API endpoints for strategy complexity optimization (F001-US002)
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.services.complexity_optimization_service import ComplexityOptimizationService
from app.models.strategy import Strategy
from app.core.dependencies import get_current_user
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["complexity"]
)

# Request/Response models
class ComplexityOptimizationRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID to optimize")
    timeframe: str = Field("1D", description="Data timeframe for analysis")
    lookback_days: int = Field(252, description="Days of historical data to analyze")
    risk_preference: str = Field("balanced", description="Risk preference: conservative, balanced, aggressive")
    
    class Config:
        schema_extra = {
            "example": {
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "timeframe": "1D",
                "lookback_days": 252,
                "risk_preference": "balanced"
            }
        }

class ComplexityOptimizationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time_seconds: int

class ComplexityScoreResponse(BaseModel):
    strategy_id: str
    current_complexity: int
    optimal_complexity: int
    recommendation: str
    confidence: float
    metrics: Dict[str, float]
    risk_adjusted_metrics: Dict[str, float]
    performance_improvement: Dict[str, float]
    timestamp: str

class ComplexityComparisonResponse(BaseModel):
    strategy_id: str
    comparisons: List[Dict[str, Any]]
    optimal_level: int
    current_level: int

class ComplexityHistoryResponse(BaseModel):
    strategy_id: str
    history: List[Dict[str, Any]]
    total_optimizations: int

# Service instance
optimization_service = ComplexityOptimizationService()

@router.post("/optimize", response_model=ComplexityOptimizationResponse)
async def optimize_complexity(
    request: ComplexityOptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Start async complexity optimization for a strategy
    
    This endpoint initiates an asynchronous optimization process that:
    1. Tests the strategy at different complexity levels (1-10)
    2. Calculates risk-adjusted returns for each level
    3. Recommends the optimal complexity based on performance metrics
    4. Stores results for future reference
    """
    try:
        # Verify strategy exists and user has access
        strategy = await db.get(Strategy, request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Start async optimization task
        task = celery_app.send_task(
            'optimize_strategy_complexity',
            args=[
                request.strategy_id,
                request.timeframe,
                request.lookback_days,
                request.risk_preference
            ]
        )
        
        # Estimate completion time based on lookback period
        estimated_time = min(300, 30 + request.lookback_days // 10)  # 30s base + time per data
        
        return ComplexityOptimizationResponse(
            task_id=task.id,
            status="processing",
            message=f"Optimization started for strategy {request.strategy_id}",
            estimated_time_seconds=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Failed to start optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/{task_id}", response_model=ComplexityScoreResponse)
async def get_optimization_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the status and results of a complexity optimization task
    """
    try:
        # Get task result from Celery
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            raise HTTPException(status_code=202, detail="Optimization still processing")
        elif task.state == 'FAILURE':
            raise HTTPException(status_code=500, detail=f"Optimization failed: {task.info}")
        elif task.state == 'SUCCESS':
            result = task.result
            return ComplexityScoreResponse(
                strategy_id=result['strategy_id'],
                current_complexity=result['current_complexity_level'],
                optimal_complexity=result['optimal_complexity_level'],
                recommendation=result['recommendation'],
                confidence=result['confidence'],
                metrics=result['metrics'],
                risk_adjusted_metrics=result['risk_adjusted_metrics'],
                performance_improvement=result['performance_improvement'],
                timestamp=result['timestamp']
            )
        else:
            raise HTTPException(status_code=202, detail=f"Task in state: {task.state}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/score/{strategy_id}", response_model=ComplexityScoreResponse)
async def get_complexity_score(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the current complexity score for a strategy
    """
    try:
        # Get strategy from database
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Return cached complexity score if available
        if strategy.optimization_metrics:
            return ComplexityScoreResponse(
                strategy_id=strategy_id,
                current_complexity=strategy.complexity_level,
                optimal_complexity=strategy.optimal_complexity or strategy.complexity_level,
                recommendation=strategy.optimization_metrics.get('score', {}).get('recommendation', ''),
                confidence=strategy.optimization_metrics.get('score', {}).get('confidence', 0),
                metrics=strategy.optimization_metrics.get('score', {}).get('metrics', {}),
                risk_adjusted_metrics=strategy.optimization_metrics.get('risk_metrics', {}),
                performance_improvement={},
                timestamp=strategy.last_optimized.isoformat() if strategy.last_optimized else datetime.utcnow().isoformat()
            )
        else:
            # No optimization data available
            raise HTTPException(
                status_code=404, 
                detail="No complexity optimization data available. Run optimization first."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get complexity score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare/{strategy_id}", response_model=ComplexityComparisonResponse)
async def compare_complexity_levels(
    strategy_id: str,
    levels: str = Query("1,2,3,4,5,6,7,8,9,10", description="Comma-separated complexity levels to compare"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Compare strategy performance at different complexity levels
    """
    try:
        # Parse complexity levels
        complexity_levels = [int(l.strip()) for l in levels.split(',')]
        
        # Get strategy
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Get comparison data from optimization metrics
        if strategy.optimization_metrics and 'all_levels_comparison' in strategy.optimization_metrics:
            comparisons = strategy.optimization_metrics['all_levels_comparison']
            
            # Filter to requested levels
            filtered_comparisons = [
                c for c in comparisons 
                if c['complexity_level'] in complexity_levels
            ]
            
            return ComplexityComparisonResponse(
                strategy_id=strategy_id,
                comparisons=filtered_comparisons,
                optimal_level=strategy.optimal_complexity or strategy.complexity_level,
                current_level=strategy.complexity_level
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="No comparison data available. Run optimization first."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare complexity levels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply/{strategy_id}")
async def apply_optimal_complexity(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Apply the recommended optimal complexity level to a strategy
    """
    try:
        # Get strategy
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Check if optimization has been run
        if not strategy.optimal_complexity:
            raise HTTPException(
                status_code=400,
                detail="No optimal complexity available. Run optimization first."
            )
        
        # Apply optimal complexity
        old_complexity = strategy.complexity_level
        strategy.complexity_level = strategy.optimal_complexity
        strategy.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "strategy_id": strategy_id,
            "previous_complexity": old_complexity,
            "new_complexity": strategy.complexity_level,
            "message": f"Complexity level updated from {old_complexity} to {strategy.complexity_level}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply optimal complexity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{strategy_id}", response_model=ComplexityHistoryResponse)
async def get_optimization_history(
    strategy_id: str,
    limit: int = Query(10, description="Number of historical optimizations to return"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the history of complexity optimizations for a strategy
    """
    try:
        # Get strategy
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # For now, return current optimization data
        # In production, this would query a separate optimization history table
        history = []
        if strategy.optimization_metrics:
            history.append({
                'timestamp': strategy.last_optimized.isoformat() if strategy.last_optimized else None,
                'optimal_complexity': strategy.optimal_complexity,
                'confidence': strategy.optimization_metrics.get('score', {}).get('confidence', 0),
                'sharpe_ratio': strategy.optimization_metrics.get('score', {}).get('metrics', {}).get('sharpe_ratio', 0),
                'risk_adjusted_return': strategy.optimization_metrics.get('risk_metrics', {}).get('risk_adjusted_return', 0)
            })
        
        return ComplexityHistoryResponse(
            strategy_id=strategy_id,
            history=history,
            total_optimizations=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-optimize")
async def batch_optimize_strategies(
    strategy_ids: List[str],
    risk_preference: str = "balanced",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Start complexity optimization for multiple strategies
    """
    try:
        tasks = []
        
        for strategy_id in strategy_ids:
            # Verify strategy exists
            strategy = await db.get(Strategy, strategy_id)
            if not strategy:
                continue
            
            # Start optimization task
            task = celery_app.send_task(
                'optimize_strategy_complexity',
                args=[strategy_id, "1D", 252, risk_preference]
            )
            
            tasks.append({
                'strategy_id': strategy_id,
                'task_id': task.id
            })
        
        return {
            'message': f"Started optimization for {len(tasks)} strategies",
            'tasks': tasks
        }
        
    except Exception as e:
        logger.error(f"Failed to start batch optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))