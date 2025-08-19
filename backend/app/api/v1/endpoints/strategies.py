"""
Strategy API endpoints
Part of F002-US001: Real Strategy Engine with Backtesting
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

from app.core.database import get_db
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
        
        # Get historical data
        price_data = await data_service.get_historical_data(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt
        )
        
        if price_data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
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
        
        price_data = await data_service.get_historical_data(
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