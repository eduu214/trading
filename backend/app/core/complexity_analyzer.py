"""
Strategy complexity analysis engine for optimal complexity scoring
Implements multi-level complexity scoring per F001-US002 requirements
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ComplexityLevel(Enum):
    """Strategy complexity levels from 1-10"""
    MINIMAL = 1      # Single indicator, basic logic
    VERY_LOW = 2     # Two indicators, simple conditions
    LOW = 3          # Multiple indicators, basic combinations
    MODERATE_LOW = 4 # Entry/exit rules with basic risk management
    MODERATE = 5     # Multi-timeframe analysis, standard patterns
    MODERATE_HIGH = 6 # Complex patterns, multiple confirmations
    HIGH = 7         # Machine learning components, adaptive logic
    VERY_HIGH = 8    # Deep learning, ensemble methods
    EXTREME = 9      # Multi-model fusion, advanced AI
    MAXIMUM = 10     # Full autonomous AI with self-optimization

@dataclass
class ComplexityMetrics:
    """Metrics for complexity scoring"""
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    recovery_time_days: float
    
    def to_dict(self) -> Dict:
        return {
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'calmar_ratio': self.calmar_ratio,
            'sortino_ratio': self.sortino_ratio,
            'recovery_time_days': self.recovery_time_days
        }

@dataclass
class ComplexityScore:
    """Complete complexity scoring result"""
    level: int
    metrics: ComplexityMetrics
    performance_score: float
    risk_score: float
    efficiency_score: float
    overall_score: float
    recommendation: str
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level,
            'metrics': self.metrics.to_dict(),
            'performance_score': self.performance_score,
            'risk_score': self.risk_score,
            'efficiency_score': self.efficiency_score,
            'overall_score': self.overall_score,
            'recommendation': self.recommendation,
            'confidence': self.confidence
        }

class ComplexityAnalyzer:
    """Core complexity analysis engine"""
    
    def __init__(self):
        self.complexity_thresholds = {
            1: {'sharpe': 0.5, 'drawdown': 0.20, 'volatility': 0.30},
            2: {'sharpe': 0.7, 'drawdown': 0.18, 'volatility': 0.28},
            3: {'sharpe': 0.9, 'drawdown': 0.16, 'volatility': 0.26},
            4: {'sharpe': 1.1, 'drawdown': 0.14, 'volatility': 0.24},
            5: {'sharpe': 1.3, 'drawdown': 0.12, 'volatility': 0.22},
            6: {'sharpe': 1.5, 'drawdown': 0.10, 'volatility': 0.20},
            7: {'sharpe': 1.7, 'drawdown': 0.08, 'volatility': 0.18},
            8: {'sharpe': 2.0, 'drawdown': 0.06, 'volatility': 0.16},
            9: {'sharpe': 2.3, 'drawdown': 0.05, 'volatility': 0.14},
            10: {'sharpe': 2.5, 'drawdown': 0.04, 'volatility': 0.12}
        }
        
    def analyze_complexity(self, 
                          returns: pd.Series,
                          strategy_params: Dict,
                          benchmark_returns: Optional[pd.Series] = None) -> ComplexityScore:
        """
        Analyze strategy complexity and return optimal complexity score
        
        Args:
            returns: Strategy returns time series
            strategy_params: Strategy configuration parameters
            benchmark_returns: Optional benchmark for comparison
            
        Returns:
            ComplexityScore with detailed metrics and recommendations
        """
        # Calculate performance metrics
        metrics = self._calculate_metrics(returns, benchmark_returns)
        
        # Score individual components
        performance_score = self._score_performance(metrics)
        risk_score = self._score_risk(metrics)
        efficiency_score = self._score_efficiency(metrics, strategy_params)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            performance_score, risk_score, efficiency_score
        )
        
        # Determine optimal complexity level
        optimal_level = self._determine_optimal_level(
            metrics, performance_score, risk_score
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            optimal_level, metrics, overall_score
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(metrics, optimal_level)
        
        return ComplexityScore(
            level=optimal_level,
            metrics=metrics,
            performance_score=performance_score,
            risk_score=risk_score,
            efficiency_score=efficiency_score,
            overall_score=overall_score,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _calculate_metrics(self, 
                          returns: pd.Series,
                          benchmark: Optional[pd.Series] = None) -> ComplexityMetrics:
        """Calculate comprehensive performance metrics"""
        
        # Basic return statistics
        daily_returns = returns.pct_change().dropna()
        
        # Sharpe Ratio (annualized)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # Maximum Drawdown
        max_drawdown = self._calculate_max_drawdown(returns)
        
        # Volatility (annualized)
        volatility = daily_returns.std() * np.sqrt(252)
        
        # Win Rate
        win_rate = (daily_returns > 0).sum() / len(daily_returns)
        
        # Profit Factor
        profit_factor = self._calculate_profit_factor(daily_returns)
        
        # Calmar Ratio
        annual_return = (returns.iloc[-1] / returns.iloc[0]) ** (252 / len(returns)) - 1
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        
        # Recovery Time
        recovery_time = self._calculate_recovery_time(returns)
        
        return ComplexityMetrics(
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            win_rate=win_rate,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            recovery_time_days=recovery_time
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252
        if returns.std() == 0:
            return 0
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        """Calculate profit factor (gross profits / gross losses)"""
        profits = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        if losses == 0:
            return float('inf') if profits > 0 else 0
        return profits / losses
    
    def _calculate_sortino_ratio(self, returns: pd.Series, target_return: float = 0) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        excess_returns = returns - target_return / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
            
        downside_deviation = np.sqrt((downside_returns ** 2).mean())
        
        if downside_deviation == 0:
            return 0
            
        return np.sqrt(252) * excess_returns.mean() / downside_deviation
    
    def _calculate_recovery_time(self, returns: pd.Series) -> float:
        """Calculate average recovery time from drawdowns in days"""
        cumulative = (1 + returns.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        # Find drawdown periods
        in_drawdown = drawdown < 0
        drawdown_periods = []
        
        start_idx = None
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = i
            elif not is_dd and start_idx is not None:
                drawdown_periods.append(i - start_idx)
                start_idx = None
        
        if drawdown_periods:
            return np.mean(drawdown_periods)
        return 0
    
    def _score_performance(self, metrics: ComplexityMetrics) -> float:
        """Score performance metrics (0-100)"""
        score = 0
        
        # Sharpe ratio contribution (30%)
        if metrics.sharpe_ratio > 2:
            score += 30
        elif metrics.sharpe_ratio > 1.5:
            score += 25
        elif metrics.sharpe_ratio > 1:
            score += 20
        elif metrics.sharpe_ratio > 0.5:
            score += 15
        else:
            score += max(0, metrics.sharpe_ratio * 30)
        
        # Win rate contribution (20%)
        score += min(20, metrics.win_rate * 40)
        
        # Profit factor contribution (20%)
        if metrics.profit_factor > 2:
            score += 20
        elif metrics.profit_factor > 1.5:
            score += 15
        elif metrics.profit_factor > 1:
            score += 10
        else:
            score += max(0, metrics.profit_factor * 10)
        
        # Calmar ratio contribution (15%)
        if metrics.calmar_ratio > 1:
            score += 15
        elif metrics.calmar_ratio > 0.5:
            score += 10
        else:
            score += max(0, metrics.calmar_ratio * 15)
        
        # Sortino ratio contribution (15%)
        if metrics.sortino_ratio > 2:
            score += 15
        elif metrics.sortino_ratio > 1:
            score += 10
        else:
            score += max(0, metrics.sortino_ratio * 7.5)
        
        return min(100, score)
    
    def _score_risk(self, metrics: ComplexityMetrics) -> float:
        """Score risk metrics (0-100, higher is better/lower risk)"""
        score = 0
        
        # Max drawdown contribution (40%)
        if metrics.max_drawdown > -0.05:
            score += 40
        elif metrics.max_drawdown > -0.10:
            score += 30
        elif metrics.max_drawdown > -0.15:
            score += 20
        elif metrics.max_drawdown > -0.20:
            score += 10
        else:
            score += max(0, (1 + metrics.max_drawdown) * 40)
        
        # Volatility contribution (30%)
        if metrics.volatility < 0.10:
            score += 30
        elif metrics.volatility < 0.15:
            score += 25
        elif metrics.volatility < 0.20:
            score += 20
        elif metrics.volatility < 0.30:
            score += 10
        else:
            score += max(0, (1 - metrics.volatility) * 30)
        
        # Recovery time contribution (30%)
        if metrics.recovery_time_days < 5:
            score += 30
        elif metrics.recovery_time_days < 10:
            score += 25
        elif metrics.recovery_time_days < 20:
            score += 20
        elif metrics.recovery_time_days < 30:
            score += 10
        else:
            score += max(0, (1 - metrics.recovery_time_days / 100) * 30)
        
        return min(100, score)
    
    def _score_efficiency(self, metrics: ComplexityMetrics, strategy_params: Dict) -> float:
        """Score efficiency based on performance vs complexity"""
        # Get parameter count as proxy for complexity
        param_count = len(strategy_params.get('indicators', [])) + \
                     len(strategy_params.get('rules', [])) + \
                     len(strategy_params.get('filters', []))
        
        # Base efficiency score
        base_score = 50
        
        # Adjust for parameter efficiency
        if param_count < 5:
            base_score += 20
        elif param_count < 10:
            base_score += 10
        elif param_count > 20:
            base_score -= 10
        
        # Adjust for performance efficiency
        perf_efficiency = metrics.sharpe_ratio / max(1, param_count / 5)
        base_score += min(30, perf_efficiency * 15)
        
        return min(100, base_score)
    
    def _calculate_overall_score(self, 
                                performance: float,
                                risk: float,
                                efficiency: float) -> float:
        """Calculate weighted overall score"""
        # Weights: Performance 40%, Risk 40%, Efficiency 20%
        return performance * 0.4 + risk * 0.4 + efficiency * 0.2
    
    def _determine_optimal_level(self,
                                metrics: ComplexityMetrics,
                                performance_score: float,
                                risk_score: float) -> int:
        """Determine optimal complexity level based on metrics"""
        
        # Start with base level based on Sharpe ratio
        if metrics.sharpe_ratio > 2.5:
            base_level = 10
        elif metrics.sharpe_ratio > 2.0:
            base_level = 8
        elif metrics.sharpe_ratio > 1.5:
            base_level = 6
        elif metrics.sharpe_ratio > 1.0:
            base_level = 4
        elif metrics.sharpe_ratio > 0.5:
            base_level = 2
        else:
            base_level = 1
        
        # Adjust for risk tolerance
        if risk_score > 80:
            base_level = max(1, base_level - 1)
        elif risk_score < 40:
            base_level = min(10, base_level + 1)
        
        # Adjust for overall performance
        if performance_score > 80:
            base_level = min(10, base_level + 1)
        elif performance_score < 40:
            base_level = max(1, base_level - 1)
        
        return base_level
    
    def _generate_recommendation(self,
                                level: int,
                                metrics: ComplexityMetrics,
                                overall_score: float) -> str:
        """Generate human-readable recommendation"""
        
        level_descriptions = {
            1: "minimal complexity with single indicator",
            2: "very low complexity with basic signals",
            3: "low complexity with simple combinations",
            4: "moderate-low complexity with risk management",
            5: "moderate complexity with multi-timeframe analysis",
            6: "moderate-high complexity with pattern recognition",
            7: "high complexity with machine learning",
            8: "very high complexity with deep learning",
            9: "extreme complexity with multi-model fusion",
            10: "maximum complexity with full AI autonomy"
        }
        
        recommendation = f"Recommended complexity level {level} ({level_descriptions[level]}). "
        
        if overall_score > 80:
            recommendation += "Excellent risk-adjusted performance achieved. "
        elif overall_score > 60:
            recommendation += "Good balance of risk and return. "
        elif overall_score > 40:
            recommendation += "Acceptable performance with room for improvement. "
        else:
            recommendation += "Consider adjusting strategy parameters. "
        
        if metrics.sharpe_ratio > 1.5:
            recommendation += f"Strong Sharpe ratio of {metrics.sharpe_ratio:.2f}. "
        
        if metrics.max_drawdown < -0.15:
            recommendation += f"Warning: High drawdown of {metrics.max_drawdown:.1%}. "
        
        return recommendation
    
    def _calculate_confidence(self, metrics: ComplexityMetrics, level: int) -> float:
        """Calculate confidence in recommendation (0-100%)"""
        confidence = 50.0
        
        # Higher Sharpe increases confidence
        if metrics.sharpe_ratio > 2:
            confidence += 20
        elif metrics.sharpe_ratio > 1.5:
            confidence += 15
        elif metrics.sharpe_ratio > 1:
            confidence += 10
        
        # Lower drawdown increases confidence
        if metrics.max_drawdown > -0.10:
            confidence += 15
        elif metrics.max_drawdown > -0.15:
            confidence += 10
        
        # Good win rate increases confidence
        if metrics.win_rate > 0.6:
            confidence += 10
        elif metrics.win_rate > 0.55:
            confidence += 5
        
        # Stable recovery time increases confidence
        if metrics.recovery_time_days < 10:
            confidence += 10
        
        return min(100, confidence)
    
    def compare_complexity_levels(self,
                                 returns_dict: Dict[int, pd.Series],
                                 strategy_params: Dict) -> Dict[int, ComplexityScore]:
        """
        Compare multiple complexity levels
        
        Args:
            returns_dict: Dictionary of complexity level -> returns series
            strategy_params: Base strategy parameters
            
        Returns:
            Dictionary of complexity level -> ComplexityScore
        """
        results = {}
        
        for level, returns in returns_dict.items():
            score = self.analyze_complexity(returns, strategy_params)
            results[level] = score
            
        return results
    
    def find_optimal_complexity(self,
                               returns_dict: Dict[int, pd.Series],
                               strategy_params: Dict,
                               risk_preference: str = 'balanced') -> Tuple[int, ComplexityScore]:
        """
        Find optimal complexity level based on risk preference
        
        Args:
            returns_dict: Dictionary of complexity level -> returns series
            strategy_params: Base strategy parameters
            risk_preference: 'conservative', 'balanced', or 'aggressive'
            
        Returns:
            Tuple of (optimal_level, ComplexityScore)
        """
        all_scores = self.compare_complexity_levels(returns_dict, strategy_params)
        
        # Weight factors based on risk preference
        if risk_preference == 'conservative':
            weights = {'risk': 0.6, 'performance': 0.3, 'efficiency': 0.1}
        elif risk_preference == 'aggressive':
            weights = {'risk': 0.2, 'performance': 0.6, 'efficiency': 0.2}
        else:  # balanced
            weights = {'risk': 0.4, 'performance': 0.4, 'efficiency': 0.2}
        
        best_level = 1
        best_weighted_score = 0
        
        for level, score in all_scores.items():
            weighted_score = (
                score.risk_score * weights['risk'] +
                score.performance_score * weights['performance'] +
                score.efficiency_score * weights['efficiency']
            )
            
            if weighted_score > best_weighted_score:
                best_weighted_score = weighted_score
                best_level = level
        
        return best_level, all_scores[best_level]