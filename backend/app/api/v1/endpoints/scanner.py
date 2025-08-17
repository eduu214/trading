from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_db, SessionLocal
from app.tasks.scanner_tasks import scan_all_markets
from app.tasks.analysis_tasks import find_uncorrelated_opportunities
from app.models.opportunity import Opportunity
from app.models.scan_result import ScanResult
from celery.result import AsyncResult

router = APIRouter()


class ScanRequest(BaseModel):
    asset_classes: List[str] = ["equities", "futures", "fx"]
    correlation_threshold: float = 0.3
    min_opportunity_score: float = 0.7
    max_results: int = 20
    min_volume: Optional[int] = None
    min_price_change: Optional[float] = None


class OpportunityResponse(BaseModel):
    id: int
    asset_class: str
    ticker: str
    opportunity_type: str
    signal_strength: float
    entry_price: float
    discovered_at: datetime
    metadata: Optional[Dict] = None

    class Config:
        orm_mode = True


class ScanStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/scan")
async def scan_markets(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger asynchronous market scan across multiple asset classes
    """
    # Prepare scan configuration
    scan_config = {}
    
    for asset_class in ["equities", "futures", "fx"]:
        if asset_class in request.asset_classes:
            config = {"enabled": True}
            
            if asset_class == "equities":
                config["min_volume"] = request.min_volume or 1000000
                config["min_price_change"] = request.min_price_change or 0.02
            elif asset_class == "futures":
                config["min_volume"] = request.min_volume or 100
                config["min_price_change"] = request.min_price_change or 0.01
            elif asset_class == "fx":
                config["min_volume"] = request.min_volume or 10000
                config["min_price_change"] = request.min_price_change or 0.005
                
            scan_config[asset_class] = config
        else:
            scan_config[asset_class] = {"enabled": False}
    
    try:
        # Trigger async scan
        task = scan_all_markets.apply_async(kwargs={"scan_config": scan_config})
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Scanning {', '.join(request.asset_classes)} markets",
            "scan_config": scan_config
        }
    except Exception as e:
        # If Celery is not available, return a test response
        return {
            "task_id": "test-task-id",
            "status": "test-mode",
            "message": f"Test mode: Would scan {', '.join(request.asset_classes)} markets",
            "scan_config": scan_config,
            "error": str(e)
        }


@router.get("/scan/{task_id}")
async def get_scan_status(task_id: str):
    """
    Get status of a running scan task
    """
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': 'Scan pending...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': 'Scan completed',
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': 'Scan failed',
            'error': str(task.info)
        }
    else:
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': f'Scan {task.state}'
        }
        
    return response


@router.get("/status")
async def get_scanner_status():
    """
    Get current scanner status and statistics
    """
    db: Session = SessionLocal()
    
    try:
        # Get recent scan statistics
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        recent_scans = db.query(ScanResult).filter(
            ScanResult.started_at >= cutoff
        ).count()
        
        opportunities_today = db.query(Opportunity).filter(
            Opportunity.discovered_at >= cutoff
        ).count()
        
        last_scan = db.query(ScanResult).order_by(
            desc(ScanResult.started_at)
        ).first()
        
        return {
            "status": "ready",
            "last_scan": last_scan.started_at if last_scan else None,
            "opportunities_found_today": opportunities_today,
            "scans_today": recent_scans
        }
    finally:
        db.close()


@router.get("/test-mock")
async def test_mock_scan():
    """
    Test endpoint with mock data to demonstrate functionality
    """
    from datetime import datetime
    import random
    
    # Generate mock opportunities
    mock_opportunities = []
    
    # Mock equities
    equity_tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    for ticker in equity_tickers:
        mock_opportunities.append({
            "ticker": ticker,
            "asset_class": "equities",
            "opportunity_type": random.choice(["momentum", "reversal", "breakout"]),
            "signal_strength": random.uniform(60, 95),
            "entry_price": random.uniform(100, 500),
            "price_change": random.uniform(-0.05, 0.05),
            "volume": random.randint(1000000, 10000000),
            "inefficiency_score": random.uniform(70, 95),
            "discovered_at": datetime.utcnow().isoformat()
        })
    
    # Mock futures
    futures_tickers = ["MES", "MNQ", "MCL"]
    for ticker in futures_tickers:
        mock_opportunities.append({
            "ticker": ticker,
            "asset_class": "futures",
            "opportunity_type": random.choice(["momentum", "reversal"]),
            "signal_strength": random.uniform(55, 85),
            "entry_price": random.uniform(4000, 5000),
            "price_change": random.uniform(-0.03, 0.03),
            "volume": random.randint(100, 1000),
            "inefficiency_score": random.uniform(65, 90),
            "discovered_at": datetime.utcnow().isoformat()
        })
    
    # Mock FX
    fx_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
    for pair in fx_pairs:
        mock_opportunities.append({
            "ticker": pair,
            "asset_class": "fx",
            "opportunity_type": random.choice(["momentum", "reversal"]),
            "signal_strength": random.uniform(50, 80),
            "entry_price": random.uniform(1.0, 1.5),
            "price_change": random.uniform(-0.01, 0.01),
            "spread": random.uniform(0.0001, 0.0005),
            "inefficiency_score": random.uniform(60, 85),
            "discovered_at": datetime.utcnow().isoformat()
        })
    
    # Sort by signal strength
    mock_opportunities.sort(key=lambda x: x["signal_strength"], reverse=True)
    
    # Find uncorrelated pairs
    uncorrelated_pairs = [
        {
            "asset1": {"ticker": "AAPL", "class": "equities"},
            "asset2": {"ticker": "EURUSD", "class": "fx"},
            "correlation": 0.12,
            "combined_score": 85.5
        },
        {
            "asset1": {"ticker": "MES", "class": "futures"},
            "asset2": {"ticker": "GBPUSD", "class": "fx"},
            "correlation": -0.08,
            "combined_score": 78.2
        }
    ]
    
    return {
        "status": "success",
        "message": "Mock data for testing",
        "opportunities_found": len(mock_opportunities),
        "opportunities": mock_opportunities[:5],  # Top 5
        "uncorrelated_pairs": uncorrelated_pairs,
        "scan_timestamp": datetime.utcnow().isoformat()
    }


@router.get("/test-scan")
async def test_scan():
    """
    Test endpoint to scan markets directly without Celery
    """
    from app.services.polygon_service import polygon_service
    import asyncio
    
    try:
        # Test getting some ticker data
        tickers = await polygon_service.get_tickers(market="stocks", active=True, limit=10)
        
        # Test scanning for opportunities
        opportunities = await polygon_service.scan_for_opportunities(
            asset_classes=["stocks"],
            min_volume=1000000,
            min_price_change=0.02
        )
        
        return {
            "status": "success",
            "tickers_found": len(tickers),
            "opportunities_found": len(opportunities),
            "sample_tickers": tickers[:3] if tickers else [],
            "sample_opportunities": opportunities[:3] if opportunities else []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    limit: int = 20,
    asset_class: Optional[str] = None,
    min_signal_strength: Optional[float] = None
):
    """
    Get recent opportunities from scans
    """
    db: Session = SessionLocal()
    
    try:
        query = db.query(Opportunity).order_by(desc(Opportunity.discovered_at))
        
        if asset_class:
            query = query.filter(Opportunity.asset_class == asset_class)
            
        if min_signal_strength:
            query = query.filter(Opportunity.signal_strength >= min_signal_strength)
            
        opportunities = query.limit(limit).all()
        
        return opportunities
    finally:
        db.close()


@router.get("/history", response_model=List[OpportunityResponse])
async def get_scan_history(
    limit: int = 100,
    asset_class: Optional[str] = None
):
    """
    Get historical scan results
    """
    return await get_opportunities(limit=limit, asset_class=asset_class)