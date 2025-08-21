"""
Strategy API endpoints
Part of F002-US001: Real Strategy Engine with Backtesting
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
import uuid
import asyncio

from app.core.database import get_db
from app.services.websocket_progress import create_websocket_progress_callback
# from app.services.polygon_service_enhanced import EnhancedPolygonService  # Will use when fully integrated

router = APIRouter()

@router.get("/test")
async def test_strategy_engine():
    """
    Test endpoint for strategy engine - generates signals from mock data
    This is a simplified version for testing without full dependencies
    """
    try:
        # Generate mock price data for testing
        days = 100
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic price movements
        np.random.seed(42)
        base_price = 100
        returns = np.random.randn(days) * 0.02  # 2% daily volatility
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLCV data
        data = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.randn(days) * 0.005),
            'high': prices * (1 + np.abs(np.random.randn(days) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(days) * 0.01)),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        })
        
        # Calculate simple indicators without TA-Lib
        # RSI calculation
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD calculation
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        sma = data['close'].rolling(window=20).mean()
        std = data['close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        # Get latest values
        current_price = data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        current_macd = macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0
        current_signal = signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0
        current_upper = upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else current_price * 1.02
        current_lower = lower_band.iloc[-1] if not pd.isna(lower_band.iloc[-1]) else current_price * 0.98
        
        # Generate test signals
        signals = []
        
        # RSI Signal
        if current_rsi < 30:
            signals.append({
                "strategy": "RSI_MEAN_REVERSION",
                "signal": "BUY",
                "strength": min(100, (30 - current_rsi) * 3),
                "reason": f"RSI oversold at {current_rsi:.2f}",
                "price": current_price
            })
        elif current_rsi > 70:
            signals.append({
                "strategy": "RSI_MEAN_REVERSION",
                "signal": "SELL",
                "strength": min(100, (current_rsi - 70) * 3),
                "reason": f"RSI overbought at {current_rsi:.2f}",
                "price": current_price
            })
        
        # MACD Signal
        if current_macd > current_signal:
            signals.append({
                "strategy": "MACD_MOMENTUM",
                "signal": "BUY",
                "strength": min(100, abs(current_macd - current_signal) * 100),
                "reason": f"MACD bullish: {current_macd:.4f} > {current_signal:.4f}",
                "price": current_price
            })
        else:
            signals.append({
                "strategy": "MACD_MOMENTUM",
                "signal": "SELL",
                "strength": min(100, abs(current_macd - current_signal) * 100),
                "reason": f"MACD bearish: {current_macd:.4f} < {current_signal:.4f}",
                "price": current_price
            })
        
        # Bollinger Band Signal
        if current_price > current_upper:
            signals.append({
                "strategy": "BOLLINGER_BREAKOUT",
                "signal": "BUY",
                "strength": min(100, ((current_price - current_upper) / current_upper) * 1000),
                "reason": f"Price {current_price:.2f} above upper band {current_upper:.2f}",
                "price": current_price
            })
        elif current_price < current_lower:
            signals.append({
                "strategy": "BOLLINGER_BREAKOUT",
                "signal": "SELL",
                "strength": min(100, ((current_lower - current_price) / current_lower) * 1000),
                "reason": f"Price {current_price:.2f} below lower band {current_lower:.2f}",
                "price": current_price
            })
        
        return {
            "status": "success",
            "message": "Strategy engine test completed",
            "data": {
                "symbol": "TEST",
                "current_price": round(current_price, 2),
                "indicators": {
                    "rsi": round(current_rsi, 2),
                    "macd": round(current_macd, 4),
                    "macd_signal": round(current_signal, 4),
                    "bb_upper": round(current_upper, 2),
                    "bb_lower": round(current_lower, 2)
                },
                "signals": signals,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in strategy engine test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available")
async def get_available_strategies():
    """Get list of available trading strategies"""
    strategies = [
        {
            "id": "rsi_mean_reversion",
            "name": "RSI Mean Reversion",
            "description": "Trades oversold/overbought conditions using RSI indicator",
            "parameters": {
                "rsi_period": 14,
                "oversold_level": 30,
                "overbought_level": 70,
                "exit_level": 50
            },
            "required_data": "OHLCV price data",
            "min_data_points": 50,
            "risk_level": "MEDIUM"
        },
        {
            "id": "macd_momentum",
            "name": "MACD Momentum",
            "description": "Captures trend changes using MACD crossovers",
            "parameters": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "required_data": "Close prices",
            "min_data_points": 100,
            "risk_level": "MEDIUM"
        },
        {
            "id": "bollinger_breakout",
            "name": "Bollinger Band Breakout",
            "description": "Trades breakouts from Bollinger Band boundaries",
            "parameters": {
                "period": 20,
                "std_dev": 2.0,
                "volume_factor": 1.5
            },
            "required_data": "OHLCV with volume",
            "min_data_points": 50,
            "risk_level": "HIGH"
        }
    ]
    
    return {
        "status": "success",
        "strategies": strategies,
        "total": len(strategies)
    }

@router.post("/{strategy_id}/backtest")
async def backtest_strategy(
    strategy_id: str,
    symbol: str = Query("AAPL", description="Symbol to backtest"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    # RSI Parameters
    rsi_period: int = Query(14, description="RSI period (2-50)"),
    oversold_level: float = Query(30, description="RSI oversold level (10-40)"),
    overbought_level: float = Query(70, description="RSI overbought level (60-90)"),
    # MACD Parameters  
    macd_fast: int = Query(12, description="MACD fast period"),
    macd_slow: int = Query(26, description="MACD slow period"),
    macd_signal: int = Query(9, description="MACD signal period"),
    # Bollinger Parameters
    bb_period: int = Query(20, description="Bollinger Band period"),
    bb_std_dev: float = Query(2.0, description="Bollinger Band standard deviations")
):
    """
    Backtest a strategy with full performance metrics
    F002-US001: Real backtesting with Vectorbt
    """
    try:
        from app.services.backtesting_engine import BacktestingEngine
        from app.services.historical_data_service import HistoricalDataService
        from datetime import datetime
        
        # Initialize services
        backtest_engine = BacktestingEngine()
        data_service = HistoricalDataService()
        
        # Parse dates
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
            
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = end_dt - timedelta(days=180)  # 6 months default
        
        # Get historical data with fallback system
        price_data, data_metadata = await data_service.get_historical_data(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt
        )
        
        if price_data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # Log data source information
        logger.info(f"Using {data_metadata['source']} data for {symbol} backtest ({data_metadata['rows']} rows)")
        
        # Run backtest based on strategy
        result = None
        if strategy_id == "rsi_mean_reversion":
            result = await backtest_engine.backtest_rsi_strategy(
                symbol, 
                price_data,
                rsi_period=rsi_period,
                oversold_level=oversold_level,
                overbought_level=overbought_level
            )
        elif strategy_id == "macd_momentum":
            result = await backtest_engine.backtest_macd_strategy(
                symbol, 
                price_data,
                fast_period=macd_fast,
                slow_period=macd_slow,
                signal_period=macd_signal
            )
        elif strategy_id == "bollinger_breakout":
            result = await backtest_engine.backtest_bollinger_strategy(
                symbol, 
                price_data,
                period=bb_period,
                std_dev=bb_std_dev
            )
        else:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Return performance metrics
        return {
            "status": "success",
            "strategy": result.strategy_name,
            "symbol": result.symbol,
            "period": {
                "start": result.start_date.isoformat(),
                "end": result.end_date.isoformat(),
                "days": (result.end_date - result.start_date).days
            },
            "performance": {
                "total_return": round(result.total_return_pct, 2),
                "sharpe_ratio": round(result.sharpe_ratio, 2),
                "max_drawdown": round(result.max_drawdown_pct, 2),
                "win_rate": round(result.win_rate * 100, 2),
                "profit_factor": round(result.profit_factor, 2)
            },
            "trades": {
                "total": result.total_trades,
                "winning": result.winning_trades,
                "losing": result.losing_trades,
                "avg_win": round(result.avg_win, 2),
                "avg_loss": round(result.avg_loss, 2),
                "best_trade": round(result.best_trade, 2),
                "worst_trade": round(result.worst_trade, 2)
            },
            "capital": {
                "initial": result.initial_capital,
                "final": round(result.final_capital, 2)
            },
            "execution_time": round(result.execution_time, 2),
            "sharpe_validation": "PASS" if result.sharpe_ratio > 1.0 else "FAIL"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backtesting {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_strategies(
    symbol: str = Query("AAPL", description="Symbol to test strategies on"),
    strategies: Optional[List[str]] = Query(None, description="List of strategy IDs to compare")
):
    """
    Compare multiple strategies on the same data
    F002-US001: Strategy comparison with sortable metrics
    """
    try:
        from app.services.backtesting_engine import BacktestingEngine
        from app.services.historical_data_service import HistoricalDataService
        from datetime import datetime
        
        # Initialize services
        backtest_engine = BacktestingEngine()
        data_service = HistoricalDataService()
        
        # Get 6 months of historical data
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=180)
        
        price_data, data_metadata = await data_service.get_historical_data(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt
        )
        
        if price_data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # If no strategies specified, test all
        if not strategies:
            strategies = ["rsi_mean_reversion", "macd_momentum", "bollinger_breakout"]
        
        # Run backtests for all strategies
        results = []
        for strategy_id in strategies:
            try:
                if strategy_id == "rsi_mean_reversion":
                    result = await backtest_engine.backtest_rsi_strategy(symbol, price_data)
                elif strategy_id == "macd_momentum":
                    result = await backtest_engine.backtest_macd_strategy(symbol, price_data)
                elif strategy_id == "bollinger_breakout":
                    result = await backtest_engine.backtest_bollinger_strategy(symbol, price_data)
                else:
                    continue
                
                results.append({
                    "strategy": result.strategy_name,
                    "sharpe_ratio": round(result.sharpe_ratio, 2),
                    "total_return": round(result.total_return_pct, 2),
                    "max_drawdown": round(result.max_drawdown_pct, 2),
                    "win_rate": round(result.win_rate * 100, 2),
                    "profit_factor": round(result.profit_factor, 2),
                    "total_trades": result.total_trades,
                    "sharpe_validation": "PASS" if result.sharpe_ratio > 1.0 else "FAIL"
                })
            except Exception as e:
                logger.error(f"Error backtesting {strategy_id}: {e}")
                results.append({
                    "strategy": strategy_id,
                    "error": str(e)
                })
        
        # Sort by Sharpe ratio (best first)
        results.sort(key=lambda x: x.get("sharpe_ratio", -999), reverse=True)
        
        # Find best strategy
        best_strategy = results[0] if results else None
        
        return {
            "status": "success",
            "symbol": symbol,
            "period": f"6 months ({start_dt.date()} to {end_dt.date()})",
            "strategies_tested": len(results),
            "best_strategy": best_strategy["strategy"] if best_strategy else None,
            "results": results,
            "recommendation": (
                f"Use {best_strategy['strategy']} with Sharpe ratio {best_strategy['sharpe_ratio']}"
                if best_strategy and best_strategy.get("sharpe_ratio", 0) > 1.0
                else "No strategy meets Sharpe ratio > 1.0 requirement"
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/stats")
async def get_system_stats():
    """
    Get backtesting system performance statistics
    F002-US001 Slice 3 Task 15: Timeout and performance monitoring
    """
    try:
        from app.services.backtesting_engine import BacktestingEngine
        from app.services.historical_data_service import HistoricalDataService
        
        # Get backtesting stats
        backtest_engine = BacktestingEngine()
        backtest_stats = await backtest_engine.get_backtest_stats()
        
        # Get data fallback stats
        data_service = HistoricalDataService()
        fallback_stats = await data_service.get_fallback_stats()
        
        return {
            "status": "success",
            "backtesting": backtest_stats,
            "data_fallback": fallback_stats,
            "system_limits": {
                "max_backtest_timeout": "300s (5 minutes)",
                "soft_timeout_warning": "240s (4 minutes)",
                "max_data_fallback_time": "5s",
                "retry_attempts": 3
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str):
    """
    Get latest strategy performance metrics
    """
    # This would query stored backtest results from database
    # For now, return instruction to use backtest endpoint
    return {
        "status": "info",
        "strategy_id": strategy_id,
        "message": "Use POST /strategies/{strategy_id}/backtest to generate performance metrics",
        "example": f"/api/v1/strategies/{strategy_id}/backtest?symbol=AAPL"
    }

@router.get("/data/quality")
async def validate_data_quality(
    symbol: str = Query("AAPL", description="Symbol to validate data quality for"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Validate data quality for a symbol
    F002-US001 Slice 3 Task 17: Data Quality Validation endpoint
    
    Checks:
    - 6-month minimum data requirement
    - Gap detection and analysis
    - Data integrity validation
    - Volume data availability
    """
    try:
        from app.services.historical_data_service import HistoricalDataService
        from datetime import datetime
        
        # Initialize data service
        data_service = HistoricalDataService()
        
        # Parse dates
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
            
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = end_dt - timedelta(days=180)  # 6 months default
        
        # Get historical data with validation
        data, metadata = await data_service.get_historical_data(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Extract validation results from metadata
        validation_passed = metadata.get('data_quality_passed', False)
        validation_details = metadata.get('validation_details', {})
        quality_warnings = metadata.get('quality_warnings', [])
        quality_errors = metadata.get('quality_errors', [])
        
        return {
            "status": "success",
            "symbol": symbol,
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "requested_days": (end_dt - start_dt).days
            },
            "data_quality": {
                "passed": validation_passed,
                "data_source": metadata.get('source', 'unknown'),
                "summary": validation_details.get('summary', {}),
                "errors": quality_errors,
                "warnings": quality_warnings
            },
            "validation_details": validation_details,
            "recommendation": (
                "Data quality is sufficient for backtesting" if validation_passed
                else f"Data quality issues detected: {', '.join(quality_errors[:3])}"
            )
        }
        
    except Exception as e:
        logger.error(f"Error validating data quality for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/backtest-with-progress")
async def backtest_strategy_with_progress(
    strategy_id: str,
    symbol: str = Query("AAPL", description="Symbol to backtest"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Start backtesting with real-time WebSocket progress updates
    Task 19: WebSocket progress updates with <1s latency
    
    Returns a task_id that can be used to subscribe to progress updates via WebSocket.
    
    WebSocket subscription example:
    ```javascript
    ws.send(JSON.stringify({
        type: "subscribe",
        task_id: "<returned_task_id>"
    }));
    ```
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        async def run_backtest_with_websocket():
            """Background task to run backtest with WebSocket updates"""
            try:
                # Create WebSocket progress callback
                ws_callback = create_websocket_progress_callback(task_id)
                
                # Send initial progress
                await ws_callback("initialization", 0.05, f"Starting backtest for {strategy_id} on {symbol}")
                await asyncio.sleep(0.5)  # Simulate some processing time
                
                # Simulate data validation phase
                await ws_callback("data_validation", 0.1, "Fetching historical data")
                await asyncio.sleep(0.8)
                await ws_callback("data_validation", 0.2, f"Loaded simulated data for {symbol}")
                await asyncio.sleep(0.5)
                
                # Simulate indicators calculation
                await ws_callback("indicators", 0.3, "Calculating RSI indicator")
                await asyncio.sleep(1.0)
                await ws_callback("indicators", 0.4, "RSI calculation complete")
                await asyncio.sleep(0.3)
                
                # Simulate signal generation
                await ws_callback("signal_generation", 0.5, "Generating trading signals")
                await asyncio.sleep(0.7)
                await ws_callback("signal_generation", 0.6, "Signal generation complete")
                await asyncio.sleep(0.4)
                
                # Simulate position simulation
                await ws_callback("position_simulation", 0.7, "Simulating position entries/exits")
                await asyncio.sleep(1.2)
                await ws_callback("position_simulation", 0.8, "Position simulation complete")
                await asyncio.sleep(0.3)
                
                # Simulate metrics calculation
                await ws_callback("metrics_calculation", 0.9, "Calculating performance metrics")
                await asyncio.sleep(0.8)
                await ws_callback("metrics_calculation", 0.95, "Metrics calculation complete")
                await asyncio.sleep(0.2)
                
                # Final completion
                await ws_callback("completion", 1.0, "Backtest completed successfully")
                
                # Send completion with simulated results
                await ws_callback.send_completion(
                    success=True,
                    result={
                        "strategy": strategy_id,
                        "symbol": symbol,
                        "metrics": {
                            "total_return": 0.1234,
                            "sharpe_ratio": 1.45,
                            "max_drawdown": -0.0567,
                            "win_rate": 0.678,
                            "total_trades": 42,
                            "profit_factor": 1.89
                        },
                        "validation_passed": True,
                        "note": "Simulated results for WebSocket demonstration"
                    }
                )
                
            except Exception as e:
                logger.error(f"Simulated backtest error for task {task_id}: {e}")
                await ws_callback.send_completion(
                    success=False,
                    error=str(e)
                )
        
        # Add background task
        background_tasks.add_task(run_backtest_with_websocket)
        
        return {
            "status": "started",
            "task_id": task_id,
            "strategy": strategy_id,
            "symbol": symbol,
            "websocket_url": "/ws",
            "subscription_message": {
                "type": "subscribe",
                "task_id": task_id
            },
            "message": "Backtest started. Connect to WebSocket and subscribe using the task_id for real-time progress updates.",
            "note": "This is a simulated backtest for WebSocket demonstration purposes"
        }
        
    except Exception as e:
        logger.error(f"Error starting backtest with progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/backtest-with-progress-full")
async def backtest_strategy_with_progress_full(
    strategy_id: str,
    symbol: str = Query("AAPL", description="Symbol to backtest"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Start backtesting with real-time WebSocket progress updates
    Task 19: WebSocket progress updates with <1s latency
    
    Returns a task_id that can be used to subscribe to progress updates via WebSocket.
    
    WebSocket subscription example:
    ```javascript
    ws.send(JSON.stringify({
        type: "subscribe",
        task_id: "<returned_task_id>"
    }));
    ```
    """
    try:
        from app.services.backtesting_engine import BacktestingEngine
        from app.services.historical_data_service import HistoricalDataService
        from app.services.technical_indicators import TechnicalIndicators
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        async def run_backtest_with_websocket():
            """Background task to run backtest with WebSocket updates"""
            try:
                # Create WebSocket progress callback
                ws_callback = create_websocket_progress_callback(task_id)
                
                # Initialize services
                data_service = HistoricalDataService()
                indicators = TechnicalIndicators()
                backtest_engine = BacktestingEngine(indicators=indicators)
                
                # Add WebSocket callback to backtesting engine
                backtest_engine.add_progress_callback(ws_callback)
                
                # Send initial progress
                await ws_callback("initialization", 0.05, f"Starting backtest for {strategy_id} on {symbol}")
                
                # Fetch historical data with progress updates
                await ws_callback("data_validation", 0.1, "Fetching historical data")
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                
                price_data = await data_service.fetch_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if price_data.empty:
                    await ws_callback.send_completion(
                        success=False,
                        error=f"No data available for {symbol}"
                    )
                    return
                
                await ws_callback("data_validation", 0.2, f"Loaded {len(price_data)} data points")
                
                # Run backtest based on strategy type
                if strategy_id == "rsi_mean_reversion":
                    result = await backtest_engine.backtest_rsi_strategy(
                        symbol=symbol,
                        price_data=price_data,
                        rsi_period=14,
                        oversold_level=30,
                        overbought_level=70
                    )
                elif strategy_id == "macd_momentum":
                    result = await backtest_engine.backtest_macd_strategy(
                        symbol=symbol,
                        price_data=price_data,
                        fast_period=12,
                        slow_period=26,
                        signal_period=9
                    )
                elif strategy_id == "bollinger_breakout":
                    result = await backtest_engine.backtest_bollinger_strategy(
                        symbol=symbol,
                        price_data=price_data,
                        period=20,
                        std_dev=2.0,
                        volume_factor=1.5
                    )
                else:
                    await ws_callback.send_completion(
                        success=False,
                        error=f"Unknown strategy: {strategy_id}"
                    )
                    return
                
                # Send completion with results
                await ws_callback.send_completion(
                    success=True,
                    result={
                        "strategy": strategy_id,
                        "symbol": symbol,
                        "metrics": {
                            "total_return": result.total_return,
                            "sharpe_ratio": result.sharpe_ratio,
                            "max_drawdown": result.max_drawdown,
                            "win_rate": result.win_rate,
                            "total_trades": result.total_trades,
                            "profit_factor": result.profit_factor
                        },
                        "validation_passed": result.sharpe_ratio > 1.0
                    }
                )
                
            except Exception as e:
                logger.error(f"Backtest error for task {task_id}: {e}")
                await ws_callback.send_completion(
                    success=False,
                    error=str(e)
                )
        
        # Add background task
        background_tasks.add_task(run_backtest_with_websocket)
        
        return {
            "status": "started",
            "task_id": task_id,
            "strategy": strategy_id,
            "symbol": symbol,
            "websocket_url": "/ws",
            "subscription_message": {
                "type": "subscribe",
                "task_id": task_id
            },
            "message": "Backtest started. Connect to WebSocket and subscribe using the task_id for real-time progress updates."
        }
        
    except Exception as e:
        logger.error(f"Error starting backtest with progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/approve")
async def approve_strategy(
    strategy_id: str,
    approval_data: Dict = None
):
    """
    Approve strategy for paper trading deployment
    Task 20: Strategy Approval Workflow with audit trail
    
    Creates audit trail and transitions strategy to paper trading phase.
    """
    try:
        from datetime import datetime
        
        # Validate strategy exists (simplified for demo)
        available_strategies = ["rsi_mean_reversion", "macd_momentum", "bollinger_breakout"]
        if strategy_id not in available_strategies:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Get approval data with defaults
        if not approval_data:
            approval_data = {}
            
        approved_by = approval_data.get("approved_by", "Admin")
        approval_date = approval_data.get("approval_date", datetime.utcnow().isoformat())
        paper_trading_enabled = approval_data.get("paper_trading_enabled", True)
        initial_capital = approval_data.get("initial_capital", 10000)
        risk_limit = approval_data.get("risk_limit", 2.0)
        notes = approval_data.get("notes", "")
        
        # Generate approval ID for audit trail
        approval_id = str(uuid.uuid4())
        
        # Create audit trail record
        audit_record = {
            "approval_id": approval_id,
            "strategy_id": strategy_id,
            "approved_by": approved_by,
            "approval_date": approval_date,
            "paper_trading_enabled": paper_trading_enabled,
            "configuration": {
                "initial_capital": initial_capital,
                "risk_limit_percent": risk_limit,
                "position_sizing": "fixed_fractional",
                "max_positions": 5
            },
            "notes": notes,
            "status": "approved",
            "deployment_stage": "paper_trading"
        }
        
        # Log the approval (in production would save to database)
        logger.info(f"Strategy approval recorded: {audit_record}")
        
        # Simulate paper trading deployment
        paper_trading_config = {
            "strategy_id": strategy_id,
            "deployment_id": str(uuid.uuid4()),
            "environment": "paper_trading",
            "initial_capital": initial_capital,
            "current_capital": initial_capital,
            "risk_limit": risk_limit,
            "positions": [],
            "performance": {
                "total_return": 0.0,
                "trades_count": 0,
                "win_rate": 0.0,
                "max_drawdown": 0.0
            },
            "status": "active",
            "deployed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Paper trading deployment initiated: {paper_trading_config}")
        
        return {
            "status": "success",
            "message": f"Strategy {strategy_id} approved for paper trading",
            "approval_id": approval_id,
            "audit_trail": audit_record,
            "paper_trading": {
                "deployment_id": paper_trading_config["deployment_id"],
                "environment": "paper_trading",
                "initial_capital": initial_capital,
                "status": "active",
                "deployed_at": paper_trading_config["deployed_at"]
            },
            "next_steps": [
                "Monitor paper trading performance",
                "Review daily/weekly reports",
                "Consider live trading approval after 30-day evaluation"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/approval-status")
async def get_approval_status(strategy_id: str):
    """
    Get current approval status and paper trading deployment info
    Task 20: Strategy approval workflow status tracking
    """
    try:
        # Simulate checking approval status (would query database in production)
        available_strategies = ["rsi_mean_reversion", "macd_momentum", "bollinger_breakout"]
        if strategy_id not in available_strategies:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Mock approval status - in production would query from database
        approval_status = {
            "strategy_id": strategy_id,
            "approval_status": "pending",  # pending, approved, rejected
            "paper_trading_status": "not_deployed",  # not_deployed, active, paused, stopped
            "last_updated": datetime.utcnow().isoformat(),
            "approvals": [],
            "paper_trading_deployments": []
        }
        
        return {
            "status": "success",
            "approval_status": approval_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approval status for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/audit-trail")
async def get_approval_audit_trail(
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip")
):
    """
    Get audit trail of all strategy approvals
    Task 20: Comprehensive audit trail for compliance
    """
    try:
        # Mock audit trail - in production would query from database
        audit_records = [
            {
                "approval_id": "audit-001",
                "strategy_id": "rsi_mean_reversion",
                "approved_by": "Admin",
                "approval_date": "2024-08-20T10:30:00Z",
                "paper_trading_enabled": True,
                "initial_capital": 10000,
                "risk_limit": 2.0,
                "status": "approved",
                "deployment_stage": "paper_trading",
                "notes": "Initial strategy approval for testing"
            }
        ]
        
        return {
            "status": "success",
            "audit_trail": audit_records,
            "pagination": {
                "total": len(audit_records),
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))