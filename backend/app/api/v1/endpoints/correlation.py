"""
Correlation Matrix API Endpoints
F001-US003 Task 3: REST endpoints for correlation data retrieval and real-time WebSocket updates

Handles:
- Correlation matrix retrieval (<500ms response)
- Real-time correlation updates via WebSocket
- Diversification score endpoints
- High correlation alerts
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import asyncio

from app.core.database import get_db
from app.services.correlation_engine import get_correlation_engine
from app.services.diversification_scorer import get_diversification_scorer

router = APIRouter()
logger = logging.getLogger(__name__)

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for topic in self.subscriptions:
            if websocket in self.subscriptions[topic]:
                self.subscriptions[topic].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, topic: str = None):
        if topic and topic in self.subscriptions:
            connections = self.subscriptions[topic]
        else:
            connections = self.active_connections
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

    def subscribe(self, websocket: WebSocket, topic: str):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if websocket not in self.subscriptions[topic]:
            self.subscriptions[topic].append(websocket)

manager = ConnectionManager()


# Request/Response Models
class CorrelationMatrixRequest(BaseModel):
    strategy_ids: Optional[List[str]] = Field(None, description="List of strategy IDs to include")
    time_period: str = Field(default="30d", description="Time period: 30d, 60d, 90d, 1y")
    method: str = Field(default="pearson", description="Correlation method: pearson, spearman, kendall")
    force_refresh: bool = Field(default=False, description="Force recalculation ignoring cache")


class CorrelationMatrixResponse(BaseModel):
    matrix_id: str
    calculated_at: str
    strategies: List[str]
    matrix: List[List[float]]
    statistics: Dict[str, float]
    high_correlations: List[Dict[str, Any]]
    cache_ttl: int
    response_time_ms: float


class DiversificationScoreRequest(BaseModel):
    portfolio_id: str = Field(default="main", description="Portfolio identifier")
    strategy_weights: Dict[str, float] = Field(..., description="Strategy weights in portfolio")
    time_period: str = Field(default="30d", description="Time period for correlation data")


class DiversificationScoreResponse(BaseModel):
    portfolio_id: str
    overall_score: float
    correlation_score: float
    num_strategies: int
    avg_correlation: float
    max_correlation: float
    high_correlation_pairs: int
    recommendations: List[str]
    calculated_at: str


class CorrelationUpdateRequest(BaseModel):
    strategy_ids: List[str] = Field(..., description="Strategy IDs to update correlations for")
    time_periods: Optional[List[str]] = Field(None, description="Time periods to calculate")
    broadcast_update: bool = Field(default=True, description="Broadcast updates via WebSocket")


# API Endpoints
@router.get("/matrix", response_model=CorrelationMatrixResponse)
async def get_correlation_matrix(
    time_period: str = "30d",
    method: str = "pearson",
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get correlation matrix for all strategies or specified subset.
    Returns data in <500ms from cache or triggers background recalculation.
    """
    start_time = datetime.utcnow()
    
    try:
        engine = get_correlation_engine()
        
        # Try to get cached matrix first
        if not force_refresh:
            cached_matrix = await engine.get_latest_correlation_matrix(db, time_period)
            
            if cached_matrix:
                # Parse matrix data
                matrix_data = cached_matrix['data']
                strategies = matrix_data['strategies']
                matrix_values = matrix_data['matrix']
                
                # Convert to pandas DataFrame for analysis
                import pandas as pd
                corr_df = pd.DataFrame(matrix_values, columns=strategies, index=strategies)
                
                # Identify high correlations
                high_correlations = engine.identify_high_correlations(corr_df)
                
                # Calculate response time
                response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return CorrelationMatrixResponse(
                    matrix_id=cached_matrix['matrix_id'],
                    calculated_at=cached_matrix['calculated_at'],
                    strategies=strategies,
                    matrix=matrix_values,
                    statistics=cached_matrix['statistics'],
                    high_correlations=high_correlations,
                    cache_ttl=900,  # 15 minutes
                    response_time_ms=response_time_ms
                )
        
        # If no cache or force refresh, trigger recalculation
        # Get default strategy list (would come from database in production)
        strategy_ids = [
            'rsi_mean_reversion',
            'macd_momentum', 
            'bollinger_breakout',
            'volume_momentum',
            'trend_following',
            'arbitrage_pairs'
        ]
        
        # Get returns data
        returns_df = engine.get_strategy_returns_data(strategy_ids, time_period)
        
        if returns_df.empty:
            raise HTTPException(status_code=404, detail="No strategy returns data available")
        
        # Calculate correlation matrix
        corr_matrix = engine.calculate_correlation_matrix(returns_df, method=method)
        
        if corr_matrix.empty:
            raise HTTPException(status_code=500, detail="Failed to calculate correlation matrix")
        
        # Store in database
        matrix_id = await engine.store_correlation_matrix(
            db, corr_matrix, time_period,
            metadata={'sample_size': len(returns_df), 'method': method}
        )
        
        # Identify high correlations
        high_correlations = engine.identify_high_correlations(corr_matrix)
        
        # Create alerts if needed
        if high_correlations:
            await engine.create_correlation_alerts(db, high_correlations)
        
        # Prepare response
        strategies = corr_matrix.columns.tolist()
        matrix_values = corr_matrix.values.tolist()
        
        # Calculate statistics
        import numpy as np
        mask = np.ones(corr_matrix.shape, dtype=bool)
        np.fill_diagonal(mask, False)
        off_diagonal = corr_matrix.values[mask]
        
        statistics = {
            'avg_correlation': float(np.mean(np.abs(off_diagonal))),
            'max_correlation': float(np.max(off_diagonal)),
            'min_correlation': float(np.min(off_diagonal)),
            'num_strategies': len(strategies)
        }
        
        # Calculate response time
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Broadcast update via WebSocket
        await manager.broadcast(
            json.dumps({
                'type': 'correlation_matrix_updated',
                'matrix_id': matrix_id,
                'time_period': time_period,
                'num_strategies': len(strategies),
                'timestamp': datetime.utcnow().isoformat()
            }),
            topic='correlations'
        )
        
        return CorrelationMatrixResponse(
            matrix_id=matrix_id,
            calculated_at=datetime.utcnow().isoformat(),
            strategies=strategies,
            matrix=matrix_values,
            statistics=statistics,
            high_correlations=high_correlations,
            cache_ttl=900,
            response_time_ms=response_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting correlation matrix: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get correlation matrix: {str(e)}")


@router.post("/update", status_code=202)
async def trigger_correlation_update(
    request: CorrelationUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger background correlation update for specified strategies.
    Returns immediately with 202 Accepted.
    """
    try:
        engine = get_correlation_engine()
        
        # Schedule background update
        background_tasks.add_task(
            run_correlation_update_task,
            db,
            request.strategy_ids,
            request.time_periods,
            request.broadcast_update
        )
        
        return {
            'status': 'accepted',
            'message': f'Correlation update scheduled for {len(request.strategy_ids)} strategies',
            'strategy_ids': request.strategy_ids,
            'time_periods': request.time_periods or ['30d', '60d', '90d', '1y']
        }
        
    except Exception as e:
        logger.error(f"Error scheduling correlation update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule update: {str(e)}")


@router.get("/diversification", response_model=DiversificationScoreResponse)
async def get_diversification_score(
    portfolio_id: str = "main",
    db: AsyncSession = Depends(get_db)
):
    """
    Get diversification score for a portfolio based on strategy correlations.
    Score ranges from 0-100 where higher is better diversified.
    """
    try:
        scorer = get_diversification_scorer()
        
        # Get portfolio data (mock for now)
        strategy_weights = {
            'rsi_mean_reversion': 0.25,
            'macd_momentum': 0.25,
            'bollinger_breakout': 0.20,
            'volume_momentum': 0.15,
            'trend_following': 0.15
        }
        
        # Calculate diversification score
        score_result = await scorer.calculate_diversification_score(
            db,
            portfolio_id=portfolio_id,
            strategy_weights=strategy_weights
        )
        
        return DiversificationScoreResponse(
            portfolio_id=portfolio_id,
            overall_score=score_result['overall_score'],
            correlation_score=score_result['correlation_score'],
            num_strategies=score_result['num_strategies'],
            avg_correlation=score_result['avg_correlation'],
            max_correlation=score_result['max_correlation'],
            high_correlation_pairs=score_result['high_correlation_pairs'],
            recommendations=score_result['recommendations'],
            calculated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error calculating diversification score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")


@router.get("/alerts")
async def get_correlation_alerts(
    active_only: bool = True,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get correlation alerts for high correlation warnings.
    """
    try:
        from sqlalchemy import select, and_
        from app.models.strategy_correlation import CorrelationAlert
        
        # Build query
        conditions = []
        if active_only:
            conditions.append(CorrelationAlert.is_active == 'Y')
        if severity:
            conditions.append(CorrelationAlert.severity == severity)
        
        query = select(CorrelationAlert)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(CorrelationAlert.created_at.desc())
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        alert_list = []
        for alert in alerts:
            alert_list.append({
                'alert_id': alert.alert_id,
                'created_at': alert.created_at.isoformat(),
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'strategy_1': alert.strategy_id_1,
                'strategy_2': alert.strategy_id_2,
                'correlation': alert.correlation_value,
                'is_active': alert.is_active == 'Y',
                'acknowledged': alert.acknowledged_at is not None
            })
        
        return {
            'alerts': alert_list,
            'total': len(alert_list),
            'active_count': sum(1 for a in alert_list if a['is_active']),
            'critical_count': sum(1 for a in alert_list if a['severity'] == 'critical')
        }
        
    except Exception as e:
        logger.error(f"Error getting correlation alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = "system",
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge a correlation alert.
    """
    try:
        from sqlalchemy import select
        from app.models.strategy_correlation import CorrelationAlert
        
        # Get alert
        result = await db.execute(
            select(CorrelationAlert).where(CorrelationAlert.alert_id == alert_id)
        )
        alert = result.scalars().first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        if notes:
            alert.resolution_notes = notes
        
        await db.commit()
        
        return {
            'status': 'success',
            'alert_id': alert_id,
            'acknowledged_at': alert.acknowledged_at.isoformat(),
            'acknowledged_by': acknowledged_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time correlation updates.
    Clients can subscribe to topics: 'correlations', 'alerts', 'diversification'
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                topic = message.get('topic', 'correlations')
                manager.subscribe(websocket, topic)
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'subscription_confirmed',
                        'topic': topic,
                        'timestamp': datetime.utcnow().isoformat()
                    }),
                    websocket
                )
            elif message.get('type') == 'ping':
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background task for correlation updates
async def run_correlation_update_task(
    db: AsyncSession,
    strategy_ids: List[str],
    time_periods: Optional[List[str]],
    broadcast_update: bool
):
    """
    Background task to run correlation updates.
    """
    try:
        engine = get_correlation_engine()
        
        # Run update
        results = await engine.run_correlation_update(db, strategy_ids, time_periods)
        
        # Broadcast results if requested
        if broadcast_update and results['success']:
            await manager.broadcast(
                json.dumps({
                    'type': 'correlation_update_complete',
                    'matrices_created': results['matrices_created'],
                    'alerts_created': results['alerts_created'],
                    'timestamp': datetime.utcnow().isoformat()
                }),
                topic='correlations'
            )
        
        logger.info(f"Correlation update completed: {results}")
        
    except Exception as e:
        logger.error(f"Error in correlation update task: {e}")
        
        # Broadcast error
        if broadcast_update:
            await manager.broadcast(
                json.dumps({
                    'type': 'correlation_update_error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }),
                topic='correlations'
            )