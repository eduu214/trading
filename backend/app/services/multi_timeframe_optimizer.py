"""
Multi-timeframe complexity optimization service
F001-US002 Slice 2: Alternative Flows implementation
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.complexity_analyzer import ComplexityAnalyzer, ComplexityScore
from app.services.complexity_optimization_service import (
    ComplexityOptimizationService,
    RiskAdjustedCalculator
)
from app.models.strategy import Strategy
from app.models.complexity_constraint import (
    ComplexityConstraint,
    ComplexityPreset,
    MultiTimeframeAnalysis,
    ConstraintType,
    TimeframeType
)
from app.services.polygon_service import PolygonService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class ConstraintEvaluator:
    """Evaluate complexity constraints"""
    
    @staticmethod
    def evaluate_constraints(
        constraints: List[ComplexityConstraint],
        metrics: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate all constraints against metrics
        
        Returns:
            Tuple of (all_satisfied, list_of_violations)
        """
        violations = []
        
        for constraint in constraints:
            if not constraint.is_active:
                continue
                
            # Map constraint type to metric value
            value = ConstraintEvaluator._get_metric_value(
                constraint.constraint_type,
                metrics
            )
            
            if value is None:
                continue
                
            # Evaluate constraint
            if not constraint.evaluate(value):
                violation_msg = (
                    f"{constraint.constraint_type.value} "
                    f"{constraint.operator} {constraint.value} "
                    f"(actual: {value:.2f})"
                )
                
                if constraint.is_hard_constraint:
                    violations.insert(0, f"[HARD] {violation_msg}")
                else:
                    violations.append(f"[SOFT] {violation_msg}")
        
        # Check if any hard constraints were violated
        hard_violations = [v for v in violations if v.startswith("[HARD]")]
        all_satisfied = len(hard_violations) == 0
        
        return all_satisfied, violations
    
    @staticmethod
    def _get_metric_value(
        constraint_type: ConstraintType,
        metrics: Dict[str, float]
    ) -> Optional[float]:
        """Map constraint type to metric value"""
        mapping = {
            ConstraintType.MIN_SHARPE: metrics.get("sharpe_ratio"),
            ConstraintType.MAX_DRAWDOWN: metrics.get("max_drawdown"),
            ConstraintType.MAX_VOLATILITY: metrics.get("volatility"),
            ConstraintType.MIN_WIN_RATE: metrics.get("win_rate"),
            ConstraintType.MIN_PROFIT_FACTOR: metrics.get("profit_factor"),
            ConstraintType.TARGET_RETURN: metrics.get("annual_return"),
            ConstraintType.RISK_LIMIT: metrics.get("value_at_risk"),
        }
        return mapping.get(constraint_type)
    
    @staticmethod
    def calculate_constraint_score(
        constraints: List[ComplexityConstraint],
        metrics: Dict[str, float]
    ) -> float:
        """
        Calculate weighted constraint satisfaction score (0-100)
        """
        if not constraints:
            return 100.0
            
        total_weight = 0
        weighted_score = 0
        
        for constraint in constraints:
            if not constraint.is_active:
                continue
                
            value = ConstraintEvaluator._get_metric_value(
                constraint.constraint_type,
                metrics
            )
            
            if value is None:
                continue
                
            weight = constraint.weight
            total_weight += weight
            
            # Calculate satisfaction score for this constraint
            if constraint.evaluate(value):
                weighted_score += weight * 100
            else:
                # Partial credit based on how close we are
                target = constraint.value
                if constraint.operator in [">", ">="]:
                    distance = max(0, target - value) / abs(target) if target != 0 else 1
                else:  # <, <=
                    distance = max(0, value - target) / abs(target) if target != 0 else 1
                
                partial_score = max(0, 100 * (1 - distance))
                weighted_score += weight * partial_score
        
        return weighted_score / total_weight if total_weight > 0 else 100.0


class MultiTimeframeOptimizer:
    """Multi-timeframe complexity optimization"""
    
    def __init__(self):
        self.analyzer = ComplexityAnalyzer()
        self.base_optimizer = ComplexityOptimizationService()
        self.risk_calculator = RiskAdjustedCalculator()
        self.constraint_evaluator = ConstraintEvaluator()
        self.polygon_service = PolygonService()
    
    async def optimize_multi_timeframe(
        self,
        strategy_id: str,
        timeframes: List[TimeframeType],
        lookback_days: int = 252,
        constraints: Optional[List[ComplexityConstraint]] = None,
        weights: Optional[Dict[str, float]] = None,
        db: AsyncSession = None
    ) -> MultiTimeframeAnalysis:
        """
        Perform multi-timeframe complexity optimization
        
        Args:
            strategy_id: Strategy to optimize
            timeframes: List of timeframes to analyze
            lookback_days: Days of historical data
            constraints: Optional complexity constraints
            weights: Optional weights for each timeframe
            db: Database session
            
        Returns:
            MultiTimeframeAnalysis with results
        """
        start_time = datetime.now()
        
        # Get strategy
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # Default weights if not provided
        if weights is None:
            weights = {tf.value: 1.0 / len(timeframes) for tf in timeframes}
        
        # Analyze each timeframe
        results = {}
        all_metrics = {}
        
        for timeframe in timeframes:
            logger.info(f"Analyzing timeframe {timeframe.value}")
            
            # Get market data for this timeframe
            market_data = await self._fetch_timeframe_data(
                strategy.symbol,
                timeframe.value,
                lookback_days
            )
            
            # Test complexity levels for this timeframe
            tf_results = await self._analyze_timeframe(
                strategy,
                market_data,
                timeframe,
                constraints
            )
            
            results[timeframe.value] = tf_results
            all_metrics[timeframe.value] = tf_results["metrics"]
        
        # Calculate weighted optimal complexity
        weighted_complexity = self._calculate_weighted_complexity(
            results,
            weights
        )
        
        # Find optimal complexity considering all timeframes
        optimal_complexity = self._determine_optimal_complexity(
            results,
            weights,
            constraints
        )
        
        # Calculate timeframe correlation
        correlation_matrix = self._calculate_timeframe_correlation(all_metrics)
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(results)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            results,
            consistency_score
        )
        
        # Create analysis record
        analysis = MultiTimeframeAnalysis(
            strategy_id=strategy_id,
            primary_timeframe=timeframes[0],
            secondary_timeframes=[tf.value for tf in timeframes[1:]],
            results=results,
            weighted_complexity=weighted_complexity,
            optimal_complexity=optimal_complexity,
            confidence_score=confidence_score,
            timeframe_correlation=correlation_matrix,
            consistency_score=consistency_score,
            analysis_duration_seconds=(datetime.now() - start_time).total_seconds()
        )
        
        # Save to database
        db.add(analysis)
        await db.commit()
        
        return analysis
    
    async def _fetch_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int
    ) -> pd.DataFrame:
        """Fetch market data for specific timeframe"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Map timeframe to multiplier and timespan
        timeframe_map = {
            "1m": (1, "minute"),
            "5m": (5, "minute"),
            "15m": (15, "minute"),
            "30m": (30, "minute"),
            "1H": (1, "hour"),
            "4H": (4, "hour"),
            "1D": (1, "day"),
            "1W": (1, "week"),
            "1M": (1, "month")
        }
        
        multiplier, timespan = timeframe_map.get(timeframe, (1, "day"))
        
        # Get data from Polygon
        bars = await self.polygon_service.get_aggregates(
            symbol,
            multiplier,
            timespan,
            start_date,
            end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': bar.timestamp,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        } for bar in bars])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    async def _analyze_timeframe(
        self,
        strategy: Strategy,
        market_data: pd.DataFrame,
        timeframe: TimeframeType,
        constraints: Optional[List[ComplexityConstraint]]
    ) -> Dict[str, Any]:
        """Analyze complexity for a specific timeframe"""
        
        # Test different complexity levels
        complexity_scores = {}
        complexity_metrics = {}
        
        for level in range(1, 11):
            # Simulate strategy at this complexity level
            returns = await self._simulate_strategy_returns(
                market_data,
                strategy.parameters,
                level
            )
            
            # Analyze complexity
            score = self.analyzer.analyze_complexity(
                returns,
                strategy.parameters
            )
            
            complexity_scores[level] = score
            complexity_metrics[level] = score.metrics.to_dict()
        
        # Find best complexity for this timeframe
        best_level = 1
        best_score = 0
        
        for level, score in complexity_scores.items():
            # Check constraints if provided
            if constraints:
                satisfied, _ = self.constraint_evaluator.evaluate_constraints(
                    constraints,
                    score.metrics.to_dict()
                )
                if not satisfied:
                    continue
            
            # Use overall score to determine best
            if score.overall_score > best_score:
                best_score = score.overall_score
                best_level = level
        
        return {
            "timeframe": timeframe.value,
            "optimal_complexity": best_level,
            "optimal_score": best_score,
            "all_scores": {
                level: score.overall_score 
                for level, score in complexity_scores.items()
            },
            "metrics": complexity_metrics[best_level],
            "constraint_satisfaction": self.constraint_evaluator.calculate_constraint_score(
                constraints or [],
                complexity_metrics[best_level]
            ) if constraints else 100.0
        }
    
    async def _simulate_strategy_returns(
        self,
        market_data: pd.DataFrame,
        parameters: Dict,
        complexity_level: int
    ) -> pd.Series:
        """Simulate strategy returns at given complexity level"""
        # This is a simplified simulation
        # In production, would use actual backtesting engine
        
        prices = market_data['close']
        returns = pd.Series(index=prices.index, dtype=float)
        
        # Simple simulation based on complexity level
        # Higher complexity = more sophisticated strategy
        if complexity_level <= 3:
            # Simple MA crossover
            ma_short = prices.rolling(window=10).mean()
            ma_long = prices.rolling(window=30).mean()
            signal = (ma_short > ma_long).astype(int)
        elif complexity_level <= 6:
            # MA + RSI
            ma_short = prices.rolling(window=20).mean()
            ma_long = prices.rolling(window=50).mean()
            rsi = self._calculate_rsi(prices)
            signal = ((ma_short > ma_long) & (rsi < 70)).astype(int)
        else:
            # Complex multi-indicator
            ma_short = prices.rolling(window=20).mean()
            ma_long = prices.rolling(window=50).mean()
            rsi = self._calculate_rsi(prices)
            bb_upper, bb_lower = self._calculate_bollinger_bands(prices)
            signal = (
                (ma_short > ma_long) & 
                (rsi < 70) & 
                (prices < bb_upper)
            ).astype(int)
        
        # Calculate returns based on signals
        position = 0
        for i in range(1, len(prices)):
            if signal.iloc[i] == 1 and signal.iloc[i-1] == 0:
                position = 1  # Buy
            elif signal.iloc[i] == 0 and signal.iloc[i-1] == 1:
                position = 0  # Sell
            
            if position == 1:
                returns.iloc[i] = prices.iloc[i] / prices.iloc[i-1] - 1
            else:
                returns.iloc[i] = 0
        
        # Convert to cumulative returns
        cumulative_returns = (1 + returns).cumprod()
        return cumulative_returns
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: int = 2
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        return upper, lower
    
    def _calculate_weighted_complexity(
        self,
        results: Dict[str, Any],
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted average complexity across timeframes"""
        weighted_sum = 0
        total_weight = 0
        
        for tf_result in results.values():
            tf = tf_result["timeframe"]
            weight = weights.get(tf, 1.0)
            weighted_sum += tf_result["optimal_complexity"] * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 5
    
    def _determine_optimal_complexity(
        self,
        results: Dict[str, Any],
        weights: Dict[str, float],
        constraints: Optional[List[ComplexityConstraint]]
    ) -> int:
        """Determine optimal complexity considering all timeframes"""
        
        # Score each complexity level across all timeframes
        level_scores = {}
        
        for level in range(1, 11):
            total_score = 0
            total_weight = 0
            
            for tf_result in results.values():
                tf = tf_result["timeframe"]
                weight = weights.get(tf, 1.0)
                
                # Get score for this level in this timeframe
                score = tf_result["all_scores"].get(level, 0)
                
                # Apply constraint satisfaction as a multiplier
                if "constraint_satisfaction" in tf_result:
                    score *= tf_result["constraint_satisfaction"] / 100
                
                total_score += score * weight
                total_weight += weight
            
            level_scores[level] = total_score / total_weight if total_weight > 0 else 0
        
        # Check complexity constraints
        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.MAX_COMPLEXITY:
                    # Remove levels above max
                    for level in range(int(constraint.value) + 1, 11):
                        level_scores.pop(level, None)
                elif constraint.constraint_type == ConstraintType.MIN_COMPLEXITY:
                    # Remove levels below min
                    for level in range(1, int(constraint.value)):
                        level_scores.pop(level, None)
        
        # Find best level
        if level_scores:
            return max(level_scores, key=level_scores.get)
        return 5  # Default middle complexity
    
    def _calculate_timeframe_correlation(
        self,
        all_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate correlation between timeframe results"""
        if len(all_metrics) < 2:
            return {}
        
        correlations = {}
        timeframes = list(all_metrics.keys())
        
        for i, tf1 in enumerate(timeframes):
            for j, tf2 in enumerate(timeframes):
                if i < j:
                    # Calculate correlation between key metrics
                    metrics1 = all_metrics[tf1]
                    metrics2 = all_metrics[tf2]
                    
                    # Use Sharpe ratio as primary correlation metric
                    corr_key = f"{tf1}_{tf2}"
                    
                    # Simple correlation based on metric similarity
                    sharpe_diff = abs(metrics1.get("sharpe_ratio", 0) - metrics2.get("sharpe_ratio", 0))
                    dd_diff = abs(metrics1.get("max_drawdown", 0) - metrics2.get("max_drawdown", 0))
                    
                    # Convert differences to correlation (0-1 scale)
                    correlation = max(0, 1 - (sharpe_diff / 3) - (dd_diff / 0.5))
                    correlations[corr_key] = correlation
        
        return correlations
    
    def _calculate_consistency_score(self, results: Dict[str, Any]) -> float:
        """Calculate how consistent results are across timeframes"""
        if len(results) < 2:
            return 1.0
        
        complexities = [r["optimal_complexity"] for r in results.values()]
        scores = [r["optimal_score"] for r in results.values()]
        
        # Calculate standard deviation of optimal complexities
        complexity_std = np.std(complexities)
        score_std = np.std(scores)
        
        # Convert to consistency score (lower std = higher consistency)
        complexity_consistency = max(0, 1 - (complexity_std / 5))  # Max std would be ~5
        score_consistency = max(0, 1 - (score_std / 50))  # Max score std ~50
        
        return (complexity_consistency + score_consistency) / 2
    
    def _calculate_confidence_score(
        self,
        results: Dict[str, Any],
        consistency_score: float
    ) -> float:
        """Calculate overall confidence in recommendation"""
        
        # Average optimal scores across timeframes
        avg_score = np.mean([r["optimal_score"] for r in results.values()])
        
        # Average constraint satisfaction
        avg_constraint_satisfaction = np.mean([
            r.get("constraint_satisfaction", 100) 
            for r in results.values()
        ])
        
        # Combine factors
        confidence = (
            (avg_score / 100) * 0.4 +  # Performance quality
            consistency_score * 0.4 +   # Consistency across timeframes
            (avg_constraint_satisfaction / 100) * 0.2  # Constraint satisfaction
        )
        
        return min(1.0, confidence)


# System preset definitions
SYSTEM_PRESETS = [
    {
        "name": "Conservative",
        "description": "Low risk, stable returns with minimal complexity",
        "risk_preference": "conservative",
        "constraints": [
            {"type": "MAX_DRAWDOWN", "operator": ">=", "value": -0.10},
            {"type": "MAX_VOLATILITY", "operator": "<=", "value": 0.15},
            {"type": "MIN_SHARPE", "operator": ">=", "value": 1.0},
            {"type": "MAX_COMPLEXITY", "operator": "<=", "value": 5}
        ]
    },
    {
        "name": "Balanced",
        "description": "Moderate risk and return with optimal complexity",
        "risk_preference": "balanced",
        "constraints": [
            {"type": "MAX_DRAWDOWN", "operator": ">=", "value": -0.15},
            {"type": "MAX_VOLATILITY", "operator": "<=", "value": 0.20},
            {"type": "MIN_SHARPE", "operator": ">=", "value": 1.2}
        ]
    },
    {
        "name": "Aggressive",
        "description": "Higher risk tolerance for maximum returns",
        "risk_preference": "aggressive",
        "constraints": [
            {"type": "MAX_DRAWDOWN", "operator": ">=", "value": -0.25},
            {"type": "MIN_SHARPE", "operator": ">=", "value": 1.5},
            {"type": "TARGET_RETURN", "operator": ">=", "value": 0.20}
        ]
    },
    {
        "name": "Scalping",
        "description": "High frequency, low complexity for quick trades",
        "risk_preference": "balanced",
        "constraints": [
            {"type": "MAX_COMPLEXITY", "operator": "<=", "value": 3},
            {"type": "MIN_WIN_RATE", "operator": ">=", "value": 0.60},
            {"type": "MAX_DRAWDOWN", "operator": ">=", "value": -0.05}
        ],
        "default_timeframe": "1m"
    },
    {
        "name": "Swing Trading",
        "description": "Medium-term positions with moderate complexity",
        "risk_preference": "balanced",
        "constraints": [
            {"type": "MIN_SHARPE", "operator": ">=", "value": 1.3},
            {"type": "MIN_PROFIT_FACTOR", "operator": ">=", "value": 1.5},
            {"type": "MAX_COMPLEXITY", "operator": "<=", "value": 7}
        ],
        "default_timeframe": "4H"
    }
]