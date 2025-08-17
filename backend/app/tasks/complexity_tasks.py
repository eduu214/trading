"""
Celery tasks for complexity optimization with timeout and retry handling
F001-US002 Slice 3: Error Handling
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
import pandas as pd

from app.tasks.celery_app import celery_app
from app.services.multi_timeframe_optimizer import MultiTimeframeOptimizer
from app.services.complexity_validation import (
    DataSufficiencyValidator,
    ConstraintValidator,
    OptimizationErrorHandler,
    FallbackComplexityScorer,
    ValidationError,
    ErrorCode
)
from app.core.database import get_db_sync
from app.models.strategy import Strategy
from app.models.complexity_constraint import ComplexityConstraint, MultiTimeframeAnalysis

logger = logging.getLogger(__name__)


class ComplexityOptimizationTask(Task):
    """Base task class with error handling"""
    
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 5,  # Initial retry delay
        'retry_backoff': True,
        'retry_backoff_max': 60
    }
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(
            f"Task {task_id} failed: {str(exc)}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "traceback": str(einfo)
            }
        )
        
        # Store failure in database
        try:
            strategy_id = args[0] if args else kwargs.get('strategy_id')
            if strategy_id:
                with get_db_sync() as db:
                    strategy = db.query(Strategy).filter_by(id=strategy_id).first()
                    if strategy:
                        strategy.optimization_metrics = strategy.optimization_metrics or {}
                        strategy.optimization_metrics['last_error'] = {
                            'error': str(exc),
                            'timestamp': datetime.utcnow().isoformat(),
                            'task_id': task_id
                        }
                        db.commit()
        except Exception as e:
            logger.error(f"Failed to store error in database: {str(e)}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(
            f"Task {task_id} retrying due to: {str(exc)}",
            extra={
                "task_id": task_id,
                "retry_count": self.request.retries
            }
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(
    base=ComplexityOptimizationTask,
    name='optimize_complexity_with_timeout',
    time_limit=300,  # Hard timeout: 5 minutes
    soft_time_limit=240  # Soft timeout: 4 minutes
)
def optimize_complexity_with_timeout(
    strategy_id: str,
    timeframe: str = "1D",
    lookback_days: int = 252,
    risk_preference: str = "balanced",
    constraints: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Optimize complexity with timeout and error handling
    
    Args:
        strategy_id: Strategy to optimize
        timeframe: Analysis timeframe
        lookback_days: Historical data period
        risk_preference: Risk preference level
        constraints: Optional constraints
        
    Returns:
        Optimization results or error details
    """
    start_time = datetime.now()
    result = {
        "success": False,
        "strategy_id": strategy_id,
        "timeframe": timeframe,
        "timestamp": start_time.isoformat()
    }
    
    try:
        # Validate constraints first
        if constraints:
            is_valid, error = ConstraintValidator.validate_constraint_compatibility(constraints)
            if not is_valid:
                raise error
        
        # Initialize optimizer
        optimizer = MultiTimeframeOptimizer()
        
        # Fetch and validate data
        logger.info(f"Fetching data for {strategy_id} on {timeframe}")
        
        with get_db_sync() as db:
            strategy = db.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                raise ValidationError(
                    f"Strategy {strategy_id} not found",
                    ErrorCode.INVALID_PARAMETERS
                )
            
            # Mock data fetch (in production, this would fetch from Polygon)
            # For now, generate sample data
            data = generate_sample_data(timeframe, lookback_days)
            
            # Validate data sufficiency
            is_valid, error = DataSufficiencyValidator.validate_data_sufficiency(
                data, timeframe, lookback_days
            )
            if not is_valid:
                raise error
            
            # Perform optimization with timeout check
            optimization_result = run_optimization_with_timeout_check(
                optimizer,
                strategy,
                data,
                timeframe,
                risk_preference,
                constraints
            )
            
            # Store results
            strategy.complexity_score = optimization_result.get("score", 0)
            strategy.optimal_complexity = optimization_result.get("optimal_complexity", 5)
            strategy.last_optimized = datetime.utcnow()
            strategy.optimization_metrics = optimization_result
            db.commit()
            
            result.update({
                "success": True,
                "optimization": optimization_result,
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            })
            
    except SoftTimeLimitExceeded:
        logger.warning(f"Optimization timeout for strategy {strategy_id}")
        
        # Use fallback scoring
        fallback = FallbackComplexityScorer.calculate_fallback_score(
            {"strategy_id": strategy_id}
        )
        
        result.update({
            "success": False,
            "error_code": ErrorCode.OPTIMIZATION_TIMEOUT,
            "message": "Optimization timed out, using fallback scoring",
            "fallback": fallback,
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        })
        
    except ValidationError as e:
        error_response = OptimizationErrorHandler.handle_optimization_error(
            e,
            {"strategy_id": strategy_id, "timeframe": timeframe},
            retry_count=optimize_complexity_with_timeout.request.retries
        )
        result.update(error_response)
        
    except Exception as e:
        logger.error(f"Unexpected error in optimization: {str(e)}")
        error_response = OptimizationErrorHandler.handle_optimization_error(
            e,
            {"strategy_id": strategy_id, "timeframe": timeframe},
            retry_count=optimize_complexity_with_timeout.request.retries
        )
        result.update(error_response)
        
        # Retry if possible
        if error_response.get("can_retry"):
            raise  # Will trigger Celery retry
    
    return result


@celery_app.task(
    base=ComplexityOptimizationTask,
    name='optimize_multi_timeframe',
    time_limit=600,  # Hard timeout: 10 minutes
    soft_time_limit=540  # Soft timeout: 9 minutes
)
def optimize_multi_timeframe_task(
    strategy_id: str,
    timeframes: List[str],
    lookback_days: int = 252,
    constraints: Optional[List[Dict]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Multi-timeframe optimization with comprehensive error handling
    """
    start_time = datetime.now()
    results = {
        "success": False,
        "strategy_id": strategy_id,
        "timeframes": timeframes,
        "timestamp": start_time.isoformat(),
        "timeframe_results": {},
        "errors": []
    }
    
    try:
        # Validate all constraints upfront
        if constraints:
            is_valid, error = ConstraintValidator.validate_constraint_compatibility(constraints)
            if not is_valid:
                raise error
        
        # Process each timeframe with error isolation
        successful_timeframes = []
        
        for timeframe in timeframes:
            try:
                logger.info(f"Processing timeframe {timeframe}")
                
                # Individual timeframe optimization
                tf_result = optimize_single_timeframe(
                    strategy_id,
                    timeframe,
                    lookback_days,
                    constraints
                )
                
                results["timeframe_results"][timeframe] = tf_result
                if tf_result.get("success"):
                    successful_timeframes.append(timeframe)
                    
            except SoftTimeLimitExceeded:
                # Timeout - stop processing remaining timeframes
                logger.warning(f"Timeout reached at timeframe {timeframe}")
                results["errors"].append({
                    "timeframe": timeframe,
                    "error": "Timeout exceeded"
                })
                break
                
            except Exception as e:
                # Log error but continue with other timeframes
                logger.error(f"Error processing timeframe {timeframe}: {str(e)}")
                results["errors"].append({
                    "timeframe": timeframe,
                    "error": str(e)
                })
                
                # Use fallback for this timeframe
                fallback = FallbackComplexityScorer.calculate_fallback_score({})
                results["timeframe_results"][timeframe] = {
                    "success": False,
                    "fallback": fallback
                }
        
        # Calculate aggregate results if we have any successful timeframes
        if successful_timeframes:
            results["success"] = True
            results["aggregate"] = calculate_aggregate_results(
                results["timeframe_results"],
                weights
            )
            
            # Store in database
            store_multi_timeframe_results(strategy_id, results)
            
        else:
            # All timeframes failed - use complete fallback
            results["fallback"] = FallbackComplexityScorer.calculate_fallback_score({})
            
    except Exception as e:
        logger.error(f"Critical error in multi-timeframe optimization: {str(e)}")
        results["error"] = str(e)
        results["error_code"] = ErrorCode.CALCULATION_ERROR
        
    finally:
        results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        results["completed_timeframes"] = len(results.get("timeframe_results", {}))
        
    return results


def run_optimization_with_timeout_check(
    optimizer,
    strategy,
    data: pd.DataFrame,
    timeframe: str,
    risk_preference: str,
    constraints: Optional[List] = None
) -> Dict[str, Any]:
    """
    Run optimization with periodic timeout checks
    """
    # This is a simplified version - in production would be more sophisticated
    
    # Calculate returns
    returns = data['close'].pct_change().dropna()
    
    # Basic metrics calculation
    metrics = {
        "sharpe_ratio": float(returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0,
        "max_drawdown": float(calculate_max_drawdown(data['close'])),
        "volatility": float(returns.std() * (252 ** 0.5)),
        "win_rate": float((returns > 0).mean()),
        "profit_factor": calculate_profit_factor(returns)
    }
    
    # Determine optimal complexity based on metrics and constraints
    optimal_complexity = determine_optimal_complexity(
        metrics,
        risk_preference,
        constraints
    )
    
    return {
        "optimal_complexity": optimal_complexity,
        "score": calculate_complexity_score(metrics, optimal_complexity),
        "metrics": metrics,
        "timeframe": timeframe,
        "risk_preference": risk_preference
    }


def optimize_single_timeframe(
    strategy_id: str,
    timeframe: str,
    lookback_days: int,
    constraints: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Optimize a single timeframe with error handling"""
    
    # Generate sample data (in production, fetch from Polygon)
    data = generate_sample_data(timeframe, lookback_days)
    
    # Validate data
    is_valid, error = DataSufficiencyValidator.validate_data_sufficiency(
        data, timeframe, lookback_days
    )
    if not is_valid:
        raise error
    
    # Perform optimization
    optimizer = MultiTimeframeOptimizer()
    result = run_optimization_with_timeout_check(
        optimizer,
        {"id": strategy_id},
        data,
        timeframe,
        "balanced",
        constraints
    )
    
    result["success"] = True
    return result


def calculate_aggregate_results(
    timeframe_results: Dict[str, Dict],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Calculate weighted aggregate results across timeframes"""
    
    successful_results = {
        tf: result for tf, result in timeframe_results.items()
        if result.get("success", False)
    }
    
    if not successful_results:
        return {}
    
    # Default equal weights if not provided
    if weights is None:
        weights = {tf: 1.0 / len(successful_results) for tf in successful_results}
    
    # Normalize weights for successful timeframes only
    total_weight = sum(weights.get(tf, 0) for tf in successful_results)
    normalized_weights = {
        tf: weights.get(tf, 0) / total_weight 
        for tf in successful_results
    }
    
    # Calculate weighted average
    weighted_complexity = sum(
        result.get("optimal_complexity", 5) * normalized_weights[tf]
        for tf, result in successful_results.items()
    )
    
    weighted_score = sum(
        result.get("score", 50) * normalized_weights[tf]
        for tf, result in successful_results.items()
    )
    
    return {
        "weighted_complexity": round(weighted_complexity, 2),
        "weighted_score": round(weighted_score, 2),
        "optimal_complexity": round(weighted_complexity),
        "timeframes_processed": list(successful_results.keys()),
        "weights_used": normalized_weights
    }


def store_multi_timeframe_results(strategy_id: str, results: Dict) -> None:
    """Store multi-timeframe results in database"""
    try:
        with get_db_sync() as db:
            analysis = MultiTimeframeAnalysis(
                strategy_id=strategy_id,
                primary_timeframe=results["timeframes"][0] if results["timeframes"] else "1D",
                secondary_timeframes=results["timeframes"][1:] if len(results["timeframes"]) > 1 else [],
                results=results["timeframe_results"],
                weighted_complexity=results.get("aggregate", {}).get("weighted_complexity"),
                optimal_complexity=results.get("aggregate", {}).get("optimal_complexity"),
                confidence_score=0.8 if results["success"] else 0.3,
                consistency_score=calculate_consistency(results["timeframe_results"]),
                analysis_duration_seconds=results.get("duration_seconds", 0)
            )
            db.add(analysis)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to store results: {str(e)}")


# Helper functions
def generate_sample_data(timeframe: str, lookback_days: int) -> pd.DataFrame:
    """Generate sample OHLCV data for testing"""
    import numpy as np
    
    # Determine number of periods based on timeframe
    periods_per_day = {
        "1m": 1440, "5m": 288, "15m": 96, "30m": 48,
        "1H": 24, "4H": 6, "1D": 1, "1W": 0.14, "1M": 0.033
    }
    
    num_periods = int(lookback_days * periods_per_day.get(timeframe, 1))
    
    # Generate random walk price data
    returns = np.random.normal(0.0001, 0.01, num_periods)
    prices = 100 * (1 + returns).cumprod()
    
    dates = pd.date_range(end=datetime.now(), periods=num_periods, freq='1H')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, num_periods)),
        'high': prices * (1 + np.random.uniform(0, 0.01, num_periods)),
        'low': prices * (1 - np.random.uniform(0, 0.01, num_periods)),
        'close': prices,
        'volume': np.random.uniform(1000000, 5000000, num_periods)
    })
    
    df.set_index('timestamp', inplace=True)
    return df


def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown"""
    cumulative = prices / prices.iloc[0]
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min())


def calculate_profit_factor(returns: pd.Series) -> float:
    """Calculate profit factor"""
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    return float(gains / losses) if losses > 0 else 1.0


def determine_optimal_complexity(
    metrics: Dict[str, float],
    risk_preference: str,
    constraints: Optional[List] = None
) -> int:
    """Determine optimal complexity level based on metrics"""
    
    # Simple heuristic based on Sharpe ratio and risk preference
    sharpe = metrics.get("sharpe_ratio", 0)
    
    if risk_preference == "conservative":
        if sharpe < 0.5:
            return 2
        elif sharpe < 1.0:
            return 3
        else:
            return 4
    elif risk_preference == "balanced":
        if sharpe < 0.5:
            return 3
        elif sharpe < 1.5:
            return 5
        else:
            return 6
    else:  # aggressive
        if sharpe < 0.5:
            return 5
        elif sharpe < 1.5:
            return 7
        else:
            return 8


def calculate_complexity_score(metrics: Dict[str, float], complexity: int) -> float:
    """Calculate overall complexity score"""
    
    # Weighted scoring based on metrics
    sharpe_score = min(100, max(0, metrics.get("sharpe_ratio", 0) * 30))
    dd_score = min(100, max(0, (1 + metrics.get("max_drawdown", -0.2)) * 50))
    vol_score = min(100, max(0, (1 - metrics.get("volatility", 0.3)) * 100))
    
    base_score = (sharpe_score + dd_score + vol_score) / 3
    
    # Adjust for complexity level
    complexity_penalty = abs(complexity - 5) * 5  # Penalty for extreme complexity
    
    return max(0, min(100, base_score - complexity_penalty))


def calculate_consistency(timeframe_results: Dict[str, Dict]) -> float:
    """Calculate consistency score across timeframes"""
    
    successful = [
        r.get("optimal_complexity", 5) 
        for r in timeframe_results.values() 
        if r.get("success", False)
    ]
    
    if len(successful) < 2:
        return 1.0
    
    # Calculate standard deviation of optimal complexities
    import numpy as np
    std_dev = np.std(successful)
    
    # Convert to consistency score (lower std = higher consistency)
    return max(0, min(1, 1 - (std_dev / 5)))