"""
Diversification Score Calculator
F001-US003 Task 5: 0-100 scale scoring algorithm based on average correlation

Handles:
- Portfolio diversification scoring
- Correlation-based diversity metrics
- Strategy type and timeframe diversity
- Recommendations for improving diversification
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json

from app.models.strategy_correlation import (
    DiversificationScore, CorrelationMatrix, StrategyCluster
)
from app.services.correlation_engine import get_correlation_engine

logger = logging.getLogger(__name__)


class DiversificationScorer:
    """Calculator for portfolio diversification scores"""
    
    def __init__(self):
        # Scoring thresholds
        self.excellent_correlation = 0.2  # < 0.2 average correlation is excellent
        self.good_correlation = 0.3       # < 0.3 is good
        self.moderate_correlation = 0.5   # < 0.5 is moderate
        self.poor_correlation = 0.7       # >= 0.7 is poor
        
        # High correlation threshold
        self.high_correlation_threshold = 0.6
        
        # Minimum strategies for good diversification
        self.min_strategies_excellent = 10
        self.min_strategies_good = 7
        self.min_strategies_moderate = 5
        
    async def calculate_diversification_score(
        self,
        db: AsyncSession,
        portfolio_id: str,
        strategy_weights: Dict[str, float],
        time_period: str = '30d'
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive diversification score for a portfolio
        
        Args:
            db: Database session
            portfolio_id: Portfolio identifier
            strategy_weights: Dictionary of strategy IDs to weights
            time_period: Time period for correlation data
            
        Returns:
            Dictionary with scores and recommendations
        """
        try:
            # Get correlation data
            engine = get_correlation_engine()
            matrix_data = await engine.get_latest_correlation_matrix(db, time_period)
            
            if not matrix_data:
                # Generate new correlation matrix if not available
                strategy_ids = list(strategy_weights.keys())
                returns_df = engine.get_strategy_returns_data(strategy_ids, time_period)
                corr_matrix = engine.calculate_correlation_matrix(returns_df)
                
                # Store for future use
                await engine.store_correlation_matrix(
                    db, corr_matrix, time_period,
                    metadata={'sample_size': len(returns_df), 'method': 'pearson'}
                )
            else:
                # Parse existing matrix
                strategies = matrix_data['data']['strategies']
                matrix_values = matrix_data['data']['matrix']
                corr_matrix = pd.DataFrame(matrix_values, columns=strategies, index=strategies)
            
            # Filter correlation matrix for portfolio strategies
            portfolio_strategies = list(strategy_weights.keys())
            available_strategies = [s for s in portfolio_strategies if s in corr_matrix.columns]
            
            if len(available_strategies) < 2:
                return self._generate_minimal_portfolio_score(portfolio_id, strategy_weights)
            
            # Get sub-matrix for portfolio strategies
            portfolio_corr = corr_matrix.loc[available_strategies, available_strategies]
            
            # Calculate correlation metrics
            correlation_metrics = self._calculate_correlation_metrics(portfolio_corr, strategy_weights)
            
            # Calculate component scores
            correlation_score = self._score_correlation_level(correlation_metrics['avg_correlation'])
            num_strategies_score = self._score_num_strategies(len(available_strategies))
            concentration_score = self._score_concentration(strategy_weights)
            
            # Calculate high correlation penalty
            high_corr_penalty = min(correlation_metrics['high_correlation_pairs'] * 5, 20)
            
            # Calculate overall score (0-100 scale)
            overall_score = (
                correlation_score * 0.4 +        # 40% weight on correlation
                num_strategies_score * 0.3 +     # 30% weight on number of strategies
                concentration_score * 0.3         # 30% weight on concentration
            ) - high_corr_penalty
            
            overall_score = max(0, min(100, overall_score))
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                correlation_metrics,
                len(available_strategies),
                strategy_weights,
                overall_score
            )
            
            # Store score in database
            await self._store_diversification_score(
                db,
                portfolio_id,
                overall_score,
                correlation_score,
                correlation_metrics,
                strategy_weights
            )
            
            return {
                'portfolio_id': portfolio_id,
                'overall_score': round(overall_score, 1),
                'correlation_score': round(correlation_score, 1),
                'num_strategies': len(available_strategies),
                'avg_correlation': round(correlation_metrics['avg_correlation'], 3),
                'max_correlation': round(correlation_metrics['max_correlation'], 3),
                'high_correlation_pairs': correlation_metrics['high_correlation_pairs'],
                'concentration_risk': round(correlation_metrics['concentration_risk'], 3),
                'recommendations': recommendations,
                'score_breakdown': {
                    'correlation_component': round(correlation_score * 0.4, 1),
                    'num_strategies_component': round(num_strategies_score * 0.3, 1),
                    'concentration_component': round(concentration_score * 0.3, 1),
                    'high_correlation_penalty': round(high_corr_penalty, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating diversification score: {e}")
            return self._generate_error_score(portfolio_id, str(e))
    
    def _calculate_correlation_metrics(
        self,
        corr_matrix: pd.DataFrame,
        strategy_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate correlation-based metrics"""
        
        # Get upper triangle of correlation matrix (excluding diagonal)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        upper_triangle = corr_matrix.where(mask)
        
        # Calculate average correlation (absolute values)
        correlations = upper_triangle.values[mask]
        avg_correlation = float(np.mean(np.abs(correlations)))
        
        # Maximum correlation
        max_correlation = float(np.max(np.abs(correlations)))
        
        # Count high correlation pairs
        high_correlation_pairs = int(np.sum(np.abs(correlations) > self.high_correlation_threshold))
        
        # Calculate weighted average correlation based on portfolio weights
        weighted_corr = 0
        total_weight = 0
        
        for strat1 in corr_matrix.columns:
            for strat2 in corr_matrix.columns:
                if strat1 != strat2 and strat1 in strategy_weights and strat2 in strategy_weights:
                    weight1 = strategy_weights.get(strat1, 0)
                    weight2 = strategy_weights.get(strat2, 0)
                    correlation = corr_matrix.loc[strat1, strat2]
                    weighted_corr += abs(correlation) * weight1 * weight2
                    total_weight += weight1 * weight2
        
        if total_weight > 0:
            weighted_avg_correlation = weighted_corr / total_weight
        else:
            weighted_avg_correlation = avg_correlation
        
        # Calculate concentration risk (Herfindahl index)
        weights = list(strategy_weights.values())
        concentration_risk = sum(w**2 for w in weights)
        
        return {
            'avg_correlation': avg_correlation,
            'weighted_avg_correlation': weighted_avg_correlation,
            'max_correlation': max_correlation,
            'high_correlation_pairs': high_correlation_pairs,
            'concentration_risk': concentration_risk
        }
    
    def _score_correlation_level(self, avg_correlation: float) -> float:
        """Score based on average correlation (0-100)"""
        
        if avg_correlation <= self.excellent_correlation:
            return 100
        elif avg_correlation <= self.good_correlation:
            # Linear interpolation between excellent and good
            return 100 - (avg_correlation - self.excellent_correlation) / (self.good_correlation - self.excellent_correlation) * 15
        elif avg_correlation <= self.moderate_correlation:
            # Linear interpolation between good and moderate
            return 85 - (avg_correlation - self.good_correlation) / (self.moderate_correlation - self.good_correlation) * 25
        elif avg_correlation <= self.poor_correlation:
            # Linear interpolation between moderate and poor
            return 60 - (avg_correlation - self.moderate_correlation) / (self.poor_correlation - self.moderate_correlation) * 30
        else:
            # Very poor correlation
            return max(0, 30 - (avg_correlation - self.poor_correlation) * 100)
    
    def _score_num_strategies(self, num_strategies: int) -> float:
        """Score based on number of strategies (0-100)"""
        
        if num_strategies >= self.min_strategies_excellent:
            return 100
        elif num_strategies >= self.min_strategies_good:
            return 85 + (num_strategies - self.min_strategies_good) / (self.min_strategies_excellent - self.min_strategies_good) * 15
        elif num_strategies >= self.min_strategies_moderate:
            return 60 + (num_strategies - self.min_strategies_moderate) / (self.min_strategies_good - self.min_strategies_moderate) * 25
        elif num_strategies >= 3:
            return 30 + (num_strategies - 3) / (self.min_strategies_moderate - 3) * 30
        elif num_strategies == 2:
            return 20
        else:
            return 0
    
    def _score_concentration(self, strategy_weights: Dict[str, float]) -> float:
        """Score based on concentration risk (0-100)"""
        
        weights = list(strategy_weights.values())
        
        # Normalize weights to sum to 1
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Calculate Herfindahl index
        herfindahl = sum(w**2 for w in weights)
        
        # Perfect diversification would be 1/n for n strategies
        n = len(weights)
        if n > 0:
            perfect_herfindahl = 1 / n
            
            # Score based on how close we are to perfect diversification
            if herfindahl <= perfect_herfindahl * 1.2:
                return 100
            elif herfindahl <= perfect_herfindahl * 1.5:
                return 85
            elif herfindahl <= perfect_herfindahl * 2:
                return 70
            elif herfindahl <= 0.5:
                return 50
            else:
                return max(0, 50 - (herfindahl - 0.5) * 100)
        
        return 0
    
    def _generate_recommendations(
        self,
        correlation_metrics: Dict[str, float],
        num_strategies: int,
        strategy_weights: Dict[str, float],
        overall_score: float
    ) -> List[str]:
        """Generate actionable recommendations for improving diversification"""
        
        recommendations = []
        
        # Score-based overall recommendation
        if overall_score >= 85:
            recommendations.append("Excellent diversification! Portfolio is well-balanced across uncorrelated strategies.")
        elif overall_score >= 70:
            recommendations.append("Good diversification. Minor improvements could enhance portfolio resilience.")
        elif overall_score >= 50:
            recommendations.append("Moderate diversification. Consider the suggestions below to reduce correlation risk.")
        else:
            recommendations.append("Poor diversification. Significant changes needed to reduce portfolio risk.")
        
        # Correlation-based recommendations
        if correlation_metrics['avg_correlation'] > self.moderate_correlation:
            recommendations.append(f"High average correlation ({correlation_metrics['avg_correlation']:.2f}). Add strategies with different market drivers.")
        
        if correlation_metrics['high_correlation_pairs'] > 0:
            recommendations.append(f"Found {correlation_metrics['high_correlation_pairs']} highly correlated pairs (>0.6). Consider replacing one strategy from each pair.")
        
        # Number of strategies recommendations
        if num_strategies < self.min_strategies_moderate:
            recommendations.append(f"Only {num_strategies} strategies in portfolio. Add {self.min_strategies_good - num_strategies} more for better diversification.")
        elif num_strategies < self.min_strategies_good:
            recommendations.append(f"Consider adding {self.min_strategies_good - num_strategies} more strategies to reach optimal diversification.")
        
        # Concentration recommendations
        max_weight = max(strategy_weights.values()) if strategy_weights else 0
        if max_weight > 0.3:
            recommendations.append(f"Largest position is {max_weight:.1%}. Consider reducing to max 30% to limit concentration risk.")
        
        min_weight = min(strategy_weights.values()) if strategy_weights else 0
        if min_weight < 0.05 and len(strategy_weights) > 5:
            recommendations.append("Some positions are very small (<5%). Consider removing or increasing them for meaningful impact.")
        
        # Specific strategy type recommendations
        if overall_score < 70:
            recommendations.append("Consider adding strategies from different categories: momentum, mean-reversion, arbitrage, or market-making.")
            recommendations.append("Diversify across timeframes: mix intraday, daily, and weekly holding periods.")
            recommendations.append("Include strategies trading different asset classes or market regimes.")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def _store_diversification_score(
        self,
        db: AsyncSession,
        portfolio_id: str,
        overall_score: float,
        correlation_score: float,
        correlation_metrics: Dict[str, float],
        strategy_weights: Dict[str, float]
    ):
        """Store diversification score in database"""
        
        try:
            score_record = DiversificationScore(
                portfolio_id=portfolio_id,
                overall_score=overall_score,
                correlation_score=correlation_score,
                num_strategies=len(strategy_weights),
                strategy_weights=strategy_weights,
                avg_correlation=correlation_metrics['avg_correlation'],
                max_correlation=correlation_metrics['max_correlation'],
                correlation_above_threshold=correlation_metrics['high_correlation_pairs'],
                concentration_risk=correlation_metrics['concentration_risk']
            )
            
            db.add(score_record)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error storing diversification score: {e}")
            await db.rollback()
    
    def _generate_minimal_portfolio_score(
        self,
        portfolio_id: str,
        strategy_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate score for portfolio with minimal strategies"""
        
        return {
            'portfolio_id': portfolio_id,
            'overall_score': 10.0,
            'correlation_score': 0.0,
            'num_strategies': len(strategy_weights),
            'avg_correlation': 0.0,
            'max_correlation': 0.0,
            'high_correlation_pairs': 0,
            'concentration_risk': 1.0,
            'recommendations': [
                "Portfolio has too few strategies for meaningful diversification.",
                f"Add at least {self.min_strategies_moderate - len(strategy_weights)} more strategies.",
                "Consider strategies with different market drivers and timeframes.",
                "Aim for strategies with correlation below 0.3 to existing positions."
            ],
            'score_breakdown': {
                'correlation_component': 0.0,
                'num_strategies_component': 10.0,
                'concentration_component': 0.0,
                'high_correlation_penalty': 0.0
            }
        }
    
    def _generate_error_score(self, portfolio_id: str, error_message: str) -> Dict[str, Any]:
        """Generate error response for score calculation"""
        
        return {
            'portfolio_id': portfolio_id,
            'overall_score': 0.0,
            'correlation_score': 0.0,
            'num_strategies': 0,
            'avg_correlation': 0.0,
            'max_correlation': 0.0,
            'high_correlation_pairs': 0,
            'concentration_risk': 0.0,
            'recommendations': [
                f"Error calculating diversification score: {error_message}",
                "Please ensure correlation data is available.",
                "Try refreshing correlation matrix calculation."
            ],
            'score_breakdown': {
                'correlation_component': 0.0,
                'num_strategies_component': 0.0,
                'concentration_component': 0.0,
                'high_correlation_penalty': 0.0
            }
        }


# Global instance
diversification_scorer = DiversificationScorer()

def get_diversification_scorer() -> DiversificationScorer:
    """Get the global diversification scorer instance"""
    return diversification_scorer