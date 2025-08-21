from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.services.portfolio_state_manager import get_portfolio_state_manager, PortfolioState, PortfolioAllocation, PortfolioStatus
from app.services.portfolio_websocket import get_portfolio_websocket_service
from app.services.mpt_optimization_engine import get_mpt_engine

router = APIRouter()
logger = logging.getLogger(__name__)


class PortfolioResponse(BaseModel):
    portfolio_id: str
    status: str
    total_value: str
    total_pnl: str
    cash_balance: str
    allocations: Dict[str, Any]
    last_updated: str
    portfolio_volatility: Optional[str] = None
    portfolio_sharpe: Optional[str] = None
    max_drawdown: Optional[str] = None
    var_1d_95: Optional[str] = None
    pending_rebalance: bool = False
    rebalance_reason: Optional[str] = None


class PortfolioConstructionRequest(BaseModel):
    portfolio_id: str = Field(default="main", description="Portfolio identifier")
    optimization_method: str = Field(default="max_sharpe", description="Optimization method: max_sharpe, min_volatility, efficient_return, efficient_risk")
    target_return: Optional[float] = Field(None, description="Target return for efficient_return method")
    target_volatility: Optional[float] = Field(None, description="Target volatility for efficient_risk method")
    constraints: Optional[Dict[str, float]] = Field(None, description="Custom constraints per strategy")
    initial_capital: float = Field(default=10000.0, description="Initial capital amount")
    rebalance_frequency: str = Field(default="monthly", description="Rebalancing frequency: daily, weekly, monthly, quarterly")
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance: conservative, moderate, aggressive")


class PortfolioConstructionResponse(BaseModel):
    portfolio_id: str
    optimization_status: str
    optimal_allocations: Dict[str, float]
    discrete_allocations: Dict[str, int]
    leftover_cash: float
    expected_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    constraints_validation: Dict[str, Any]
    rebalancing_schedule: Dict[str, Any]
    construction_timestamp: str


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: str = "main"):
    """Get portfolio overview with real-time WebSocket integration"""
    try:
        manager = await get_portfolio_state_manager()
        portfolio_state = await manager.get_portfolio_state(portfolio_id)
        
        if not portfolio_state:
            # Return default portfolio structure
            return PortfolioResponse(
                portfolio_id=portfolio_id,
                status="inactive",
                total_value="0.00",
                total_pnl="0.00",
                cash_balance="10000.00",
                allocations={},
                last_updated=datetime.utcnow().isoformat(),
                pending_rebalance=False
            )
        
        # Convert PortfolioState to response format
        return PortfolioResponse(
            portfolio_id=portfolio_state.portfolio_id,
            status=portfolio_state.status.value,
            total_value=str(portfolio_state.total_value),
            total_pnl=str(portfolio_state.total_pnl),
            cash_balance=str(portfolio_state.cash_balance),
            allocations={
                strategy_id: {
                    "strategy_id": alloc.strategy_id,
                    "current_weight": str(alloc.current_weight),
                    "target_weight": str(alloc.target_weight),
                    "market_value": str(alloc.market_value),
                    "unrealized_pnl": str(alloc.unrealized_pnl),
                    "last_updated": alloc.last_updated.isoformat(),
                    "drift_percentage": str(alloc.drift_percentage),
                    "allocation_status": alloc.allocation_status
                }
                for strategy_id, alloc in portfolio_state.allocations.items()
            },
            last_updated=portfolio_state.last_updated.isoformat(),
            portfolio_volatility=str(portfolio_state.portfolio_volatility) if portfolio_state.portfolio_volatility else None,
            portfolio_sharpe=str(portfolio_state.portfolio_sharpe) if portfolio_state.portfolio_sharpe else None,
            max_drawdown=str(portfolio_state.max_drawdown) if portfolio_state.max_drawdown else None,
            var_1d_95=str(portfolio_state.var_1d_95) if portfolio_state.var_1d_95 else None,
            pending_rebalance=portfolio_state.pending_rebalance,
            rebalance_reason=portfolio_state.rebalance_reason
        )
        
    except Exception as e:
        logger.error(f"Error getting portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")


@router.get("/pnl")
async def get_portfolio_pnl(portfolio_id: str = "main"):
    """Get real-time portfolio P&L breakdown"""
    try:
        manager = await get_portfolio_state_manager()
        pnl_data = await manager.get_real_time_pnl(portfolio_id)
        
        total_pnl = sum(pnl_data.values())
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "strategy_pnl": {k: str(v) for k, v in pnl_data.items()},
            "total_pnl": str(total_pnl),
            "last_updated": datetime.utcnow().isoformat(),
            "websocket_url": "/ws",
            "websocket_subscribe": {
                "type": "subscribe_portfolio",
                "portfolio_id": portfolio_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting P&L for portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get P&L: {str(e)}")


@router.post("/test/update-pnl")
async def test_update_portfolio_pnl(
    portfolio_id: str = "main",
    strategy_id: str = "rsi_mean_reversion",
    unrealized_pnl: float = 150.0,
    realized_pnl: float = 50.0
):
    """Test endpoint to update portfolio P&L and trigger WebSocket updates"""
    try:
        manager = await get_portfolio_state_manager()
        portfolio_ws = await get_portfolio_websocket_service()
        
        # Update P&L in Redis
        success = await manager.update_strategy_pnl(
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            unrealized_pnl=Decimal(str(unrealized_pnl)),
            realized_pnl=Decimal(str(realized_pnl))
        )
        
        if success:
            # Get updated P&L data
            pnl_data = await manager.get_real_time_pnl(portfolio_id)
            
            # Broadcast P&L update via WebSocket
            await portfolio_ws.broadcast_pnl_update(portfolio_id, pnl_data)
            
            return {
                "status": "success",
                "message": "P&L updated and broadcasted via WebSocket",
                "portfolio_id": portfolio_id,
                "strategy_id": strategy_id,
                "updated_pnl": {
                    "unrealized": str(unrealized_pnl),
                    "realized": str(realized_pnl),
                    "total": str(unrealized_pnl + realized_pnl)
                },
                "total_portfolio_pnl": str(sum(pnl_data.values())),
                "websocket_url": "/ws",
                "note": "Real-time update sent to all subscribers"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update P&L")
            
    except Exception as e:
        logger.error(f"Error updating portfolio P&L: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update P&L: {str(e)}")


@router.post("/test/simulate-state")
async def simulate_portfolio_state(portfolio_id: str = "main"):
    """Test endpoint to create a sample portfolio state and broadcast via WebSocket"""
    try:
        manager = await get_portfolio_state_manager()
        portfolio_ws = await get_portfolio_websocket_service()
        
        # Create sample portfolio state
        sample_allocations = {
            'rsi_mean_reversion': PortfolioAllocation(
                strategy_id='rsi_mean_reversion',
                current_weight=Decimal('0.40'),
                target_weight=Decimal('0.35'),
                market_value=Decimal('4000.00'),
                unrealized_pnl=Decimal('150.00'),
                last_updated=datetime.utcnow()
            ),
            'macd_momentum': PortfolioAllocation(
                strategy_id='macd_momentum',
                current_weight=Decimal('0.35'),
                target_weight=Decimal('0.40'),
                market_value=Decimal('3500.00'),
                unrealized_pnl=Decimal('200.00'),
                last_updated=datetime.utcnow()
            ),
            'bollinger_breakout': PortfolioAllocation(
                strategy_id='bollinger_breakout',
                current_weight=Decimal('0.25'),
                target_weight=Decimal('0.25'),
                market_value=Decimal('2500.00'),
                unrealized_pnl=Decimal('-50.00'),
                last_updated=datetime.utcnow()
            )
        }
        
        portfolio_state = PortfolioState(
            portfolio_id=portfolio_id,
            status=PortfolioStatus.ACTIVE,
            total_value=Decimal('10000.00'),
            total_pnl=Decimal('300.00'),
            cash_balance=Decimal('0.00'),
            allocations=sample_allocations,
            last_updated=datetime.utcnow(),
            portfolio_volatility=Decimal('0.15'),
            portfolio_sharpe=Decimal('1.25'),
            max_drawdown=Decimal('0.08'),
            var_1d_95=Decimal('150.00')
        )
        
        # Store the state
        success = await manager.update_portfolio_state(portfolio_state)
        
        if success:
            # Broadcast portfolio state update via WebSocket
            await portfolio_ws.broadcast_portfolio_update(
                portfolio_id=portfolio_id,
                update_type="state",
                data=portfolio_ws._serialize_portfolio_state(portfolio_state)
            )
            
            return {
                "status": "success",
                "message": "Sample portfolio state created and broadcasted",
                "portfolio_id": portfolio_id,
                "portfolio_state": portfolio_ws._serialize_portfolio_state(portfolio_state),
                "websocket_url": "/ws",
                "note": "Connect to WebSocket and subscribe to portfolio updates"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store portfolio state")
            
    except Exception as e:
        logger.error(f"Error simulating portfolio state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate state: {str(e)}")


@router.post("/optimize")
async def optimize_portfolio_mpt(
    optimization_method: str = "max_sharpe",
    target_return: Optional[float] = None,
    target_volatility: Optional[float] = None,
    portfolio_id: str = "main"
):
    """Portfolio optimization using Modern Portfolio Theory"""
    try:
        mpt_engine = get_mpt_engine()
        portfolio_ws = await get_portfolio_websocket_service()
        
        # Get strategy returns data
        strategy_returns = mpt_engine.get_strategy_returns_data(portfolio_id)
        
        if strategy_returns.empty:
            raise HTTPException(status_code=400, detail="No strategy returns data available")
        
        # Perform optimization
        optimization_result = mpt_engine.optimize_portfolio(
            strategy_returns=strategy_returns,
            optimization_method=optimization_method,
            target_return=target_return,
            target_volatility=target_volatility
        )
        
        if optimization_result.get('success'):
            # Broadcast optimization result via WebSocket
            await portfolio_ws.broadcast_portfolio_update(
                portfolio_id=portfolio_id,
                update_type="optimization_result",
                data=optimization_result
            )
            
            return {
                "status": "success",
                "portfolio_id": portfolio_id,
                "optimization_result": optimization_result,
                "websocket_url": "/ws",
                "note": "Optimization completed using Modern Portfolio Theory"
            }
        else:
            raise HTTPException(status_code=500, detail=optimization_result.get('error', 'Optimization failed'))
            
    except Exception as e:
        logger.error(f"Error in MPT optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/efficient-frontier")
async def get_efficient_frontier(
    portfolio_id: str = "main",
    n_points: int = 50
):
    """Calculate efficient frontier for portfolio visualization"""
    try:
        mpt_engine = get_mpt_engine()
        
        # Get strategy returns data
        strategy_returns = mpt_engine.get_strategy_returns_data(portfolio_id)
        
        if strategy_returns.empty:
            raise HTTPException(status_code=400, detail="No strategy returns data available")
        
        # Calculate efficient frontier
        frontier_data = mpt_engine.calculate_efficient_frontier(
            strategy_returns=strategy_returns,
            n_points=n_points
        )
        
        # Clean the data for JSON serialization
        import json
        import numpy as np
        
        def clean_for_json(obj):
            """Recursively clean object for JSON serialization"""
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, (float, np.float64, np.float32)):
                if np.isnan(obj) or np.isinf(obj):
                    return 0.0
                return float(obj)
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            else:
                return obj
        
        cleaned_data = clean_for_json(frontier_data)
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "efficient_frontier": cleaned_data,
            "calculation_timestamp": datetime.utcnow().isoformat(),
            "note": "Use this data for efficient frontier chart visualization"
        }
        
    except Exception as e:
        logger.error(f"Error calculating efficient frontier: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate efficient frontier: {str(e)}")


@router.post("/validate-allocation")
async def validate_portfolio_allocation(
    allocation: Dict[str, float],
    portfolio_id: str = "main"
):
    """Validate portfolio allocation against constraints"""
    try:
        mpt_engine = get_mpt_engine()
        
        # Validate allocation
        validation_result = mpt_engine.validate_allocation_constraints(allocation)
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "allocation": allocation,
            "validation_result": validation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating allocation: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/construct", response_model=PortfolioConstructionResponse)
async def construct_portfolio(
    request: PortfolioConstructionRequest,
    background_tasks: BackgroundTasks
):
    """
    Complete portfolio construction endpoint with optimization, validation, and scheduling.
    Combines MPT optimization with practical portfolio construction constraints.
    """
    try:
        mpt_engine = get_mpt_engine()
        manager = await get_portfolio_state_manager()
        portfolio_ws = await get_portfolio_websocket_service()
        
        # Get strategy returns data
        strategy_returns = mpt_engine.get_strategy_returns_data(request.portfolio_id)
        
        if strategy_returns.empty:
            raise HTTPException(status_code=400, detail="No strategy returns data available")
        
        # Apply risk tolerance adjustments
        risk_multiplier = {
            "conservative": 0.7,
            "moderate": 1.0,
            "aggressive": 1.3
        }.get(request.risk_tolerance, 1.0)
        
        # Perform portfolio optimization
        optimization_result = mpt_engine.optimize_portfolio(
            strategy_returns=strategy_returns,
            optimization_method=request.optimization_method,
            target_return=request.target_return,
            target_volatility=request.target_volatility,
            custom_constraints=request.constraints
        )
        
        if not optimization_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=optimization_result.get('error', 'Optimization failed')
            )
        
        # Validate allocations
        validation_result = mpt_engine.validate_allocation_constraints(
            optimization_result['optimal_weights'],
            custom_constraints={"risk_tolerance": {"max_weight": 0.30 * risk_multiplier}}
        )
        
        # Calculate rebalancing schedule
        rebalance_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90
        }.get(request.rebalance_frequency, 30)
        
        next_rebalance = datetime.utcnow() + timedelta(days=rebalance_days)
        
        rebalancing_schedule = {
            "frequency": request.rebalance_frequency,
            "next_rebalance": next_rebalance.isoformat(),
            "drift_threshold": 0.05,  # 5% drift threshold
            "auto_rebalance": True
        }
        
        # Create portfolio state
        allocations = {}
        for strategy_id, weight in optimization_result['optimal_weights'].items():
            allocations[strategy_id] = PortfolioAllocation(
                strategy_id=strategy_id,
                current_weight=Decimal(str(weight)),
                target_weight=Decimal(str(weight)),
                market_value=Decimal(str(request.initial_capital * weight)),
                unrealized_pnl=Decimal('0'),
                last_updated=datetime.utcnow()
            )
        
        portfolio_state = PortfolioState(
            portfolio_id=request.portfolio_id,
            status=PortfolioStatus.ACTIVE,
            total_value=Decimal(str(request.initial_capital)),
            total_pnl=Decimal('0'),
            cash_balance=Decimal(str(optimization_result.get('leftover_cash', 0))),
            allocations=allocations,
            last_updated=datetime.utcnow(),
            portfolio_volatility=Decimal(str(optimization_result['performance_metrics']['annual_volatility'])),
            portfolio_sharpe=Decimal(str(optimization_result['performance_metrics']['sharpe_ratio'])),
            max_drawdown=Decimal(str(optimization_result['performance_metrics']['max_drawdown'])),
            var_1d_95=Decimal(str(optimization_result['performance_metrics']['var_95']))
        )
        
        # Store portfolio state
        await manager.update_portfolio_state(portfolio_state)
        
        # Broadcast construction complete via WebSocket
        await portfolio_ws.broadcast_portfolio_update(
            portfolio_id=request.portfolio_id,
            update_type="portfolio_constructed",
            data={
                "status": "success",
                "optimal_allocations": optimization_result['optimal_weights'],
                "expected_return": optimization_result['performance_metrics']['expected_annual_return'],
                "sharpe_ratio": optimization_result['performance_metrics']['sharpe_ratio']
            }
        )
        
        # Schedule background rebalancing check
        background_tasks.add_task(
            manager.check_rebalancing_needed,
            request.portfolio_id,
            0.05  # 5% drift threshold
        )
        
        return PortfolioConstructionResponse(
            portfolio_id=request.portfolio_id,
            optimization_status="success",
            optimal_allocations=optimization_result['optimal_weights'],
            discrete_allocations=optimization_result.get('discrete_allocation', {}),
            leftover_cash=optimization_result.get('leftover_cash', 0),
            expected_metrics={
                "expected_annual_return": optimization_result['performance_metrics']['expected_annual_return'],
                "annual_volatility": optimization_result['performance_metrics']['annual_volatility'],
                "sharpe_ratio": optimization_result['performance_metrics']['sharpe_ratio'],
                "sortino_ratio": optimization_result['performance_metrics'].get('sortino_ratio', 0)
            },
            risk_metrics={
                "max_drawdown": optimization_result['performance_metrics']['max_drawdown'],
                "var_95": optimization_result['performance_metrics']['var_95'],
                "cvar_95": optimization_result['performance_metrics'].get('cvar_95', 0)
            },
            constraints_validation=validation_result,
            rebalancing_schedule=rebalancing_schedule,
            construction_timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in portfolio construction: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio construction failed: {str(e)}")


@router.get("/metrics")
async def get_portfolio_metrics(
    allocation: Optional[str] = None,
    portfolio_id: str = "main"
):
    """Calculate portfolio metrics for given allocation"""
    try:
        mpt_engine = get_mpt_engine()
        
        # Parse allocation if provided
        if allocation:
            import json
            allocation_dict = json.loads(allocation)
        else:
            # Use current portfolio allocation
            manager = await get_portfolio_state_manager()
            portfolio_state = await manager.get_portfolio_state(portfolio_id)
            
            if portfolio_state and portfolio_state.allocations:
                allocation_dict = {
                    strategy_id: float(alloc.current_weight) 
                    for strategy_id, alloc in portfolio_state.allocations.items()
                }
            else:
                raise HTTPException(status_code=400, detail="No allocation provided and no current portfolio state")
        
        # Get strategy returns
        strategy_returns = mpt_engine.get_strategy_returns_data(portfolio_id)
        
        if strategy_returns.empty:
            raise HTTPException(status_code=400, detail="No strategy returns data available")
        
        # Calculate portfolio returns
        portfolio_returns = (strategy_returns * pd.Series(allocation_dict)).sum(axis=1)
        
        # Calculate metrics
        additional_metrics = mpt_engine._calculate_additional_metrics(portfolio_returns)
        
        # Basic metrics
        annual_return = portfolio_returns.mean() * 252
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - mpt_engine.risk_free_rate) / annual_volatility
        
        metrics = {
            'expected_annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            **additional_metrics
        }
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "allocation": allocation_dict,
            "metrics": metrics,
            "calculation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")