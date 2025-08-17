"""
Cross-asset correlation analysis for finding uncorrelated opportunities
"""
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """Analyzes correlations between different assets and asset classes"""
    
    def __init__(self):
        self.min_data_points = 20  # Minimum data points for correlation
        self.correlation_threshold = 0.3  # Below this is considered uncorrelated
        
    def calculate_correlation(
        self,
        series1: List[float],
        series2: List[float]
    ) -> Optional[float]:
        """
        Calculate Pearson correlation coefficient between two price series
        """
        if len(series1) != len(series2) or len(series1) < self.min_data_points:
            return None
            
        try:
            # Calculate returns instead of raw prices for better correlation analysis
            returns1 = self._calculate_returns(series1)
            returns2 = self._calculate_returns(series2)
            
            if len(returns1) < 2 or len(returns2) < 2:
                return None
                
            correlation, _ = stats.pearsonr(returns1, returns2)
            return correlation
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return None
            
    def calculate_correlation_matrix(
        self,
        assets: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for multiple assets
        """
        matrix = {}
        asset_names = list(assets.keys())
        
        for i, asset1 in enumerate(asset_names):
            matrix[asset1] = {}
            
            for j, asset2 in enumerate(asset_names):
                if i == j:
                    matrix[asset1][asset2] = 1.0
                elif j < i:
                    # Use already calculated value (matrix is symmetric)
                    matrix[asset1][asset2] = matrix[asset2][asset1]
                else:
                    correlation = self.calculate_correlation(
                        assets[asset1],
                        assets[asset2]
                    )
                    matrix[asset1][asset2] = correlation if correlation is not None else 0.0
                    
        return matrix
        
    def find_uncorrelated_pairs(
        self,
        assets: Dict[str, List[float]],
        max_correlation: float = None
    ) -> List[Dict]:
        """
        Find pairs of assets with low correlation
        """
        if max_correlation is None:
            max_correlation = self.correlation_threshold
            
        correlation_matrix = self.calculate_correlation_matrix(assets)
        uncorrelated_pairs = []
        
        asset_names = list(assets.keys())
        
        for i, asset1 in enumerate(asset_names):
            for j, asset2 in enumerate(asset_names[i+1:], i+1):
                correlation = correlation_matrix[asset1][asset2]
                
                if abs(correlation) <= max_correlation:
                    uncorrelated_pairs.append({
                        "asset1": asset1,
                        "asset2": asset2,
                        "correlation": correlation,
                        "relationship": self._classify_correlation(correlation)
                    })
                    
        # Sort by absolute correlation (most uncorrelated first)
        uncorrelated_pairs.sort(key=lambda x: abs(x["correlation"]))
        
        return uncorrelated_pairs
        
    def analyze_cross_asset_opportunities(
        self,
        opportunities: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Analyze opportunities across asset classes to find uncorrelated trades
        """
        cross_asset_opportunities = []
        
        # Extract price data for correlation analysis
        asset_prices = {}
        asset_metadata = {}
        
        for asset_class, opps in opportunities.items():
            for opp in opps:
                ticker = opp["ticker"]
                
                # Store metadata
                asset_metadata[ticker] = {
                    "asset_class": asset_class,
                    "opportunity": opp
                }
                
                # For correlation, we need historical prices (simplified for now)
                # In production, we'd fetch full historical data
                if "close" in opp:
                    # Create synthetic price series based on recent change
                    base_price = opp["close"]
                    price_change = opp.get("price_change", 0)
                    
                    # Generate synthetic historical prices
                    prices = []
                    for i in range(30):
                        # Add some random variation
                        variation = np.random.normal(0, abs(price_change) * 0.1)
                        historical_price = base_price * (1 - price_change * (30-i)/30) * (1 + variation)
                        prices.append(historical_price)
                    
                    asset_prices[ticker] = prices
                    
        # Find uncorrelated pairs
        if len(asset_prices) >= 2:
            uncorrelated_pairs = self.find_uncorrelated_pairs(asset_prices)
            
            for pair in uncorrelated_pairs[:10]:  # Top 10 uncorrelated pairs
                asset1_meta = asset_metadata[pair["asset1"]]
                asset2_meta = asset_metadata[pair["asset2"]]
                
                # Calculate combined opportunity score
                score1 = asset1_meta["opportunity"].get("inefficiency_score", 50)
                score2 = asset2_meta["opportunity"].get("inefficiency_score", 50)
                
                # Bonus for being in different asset classes
                cross_class_bonus = 1.2 if asset1_meta["asset_class"] != asset2_meta["asset_class"] else 1.0
                
                combined_score = ((score1 + score2) / 2) * cross_class_bonus * (1 - abs(pair["correlation"]))
                
                cross_asset_opportunities.append({
                    "type": "uncorrelated_pair",
                    "asset1": {
                        "ticker": pair["asset1"],
                        "class": asset1_meta["asset_class"],
                        "opportunity": asset1_meta["opportunity"]
                    },
                    "asset2": {
                        "ticker": pair["asset2"],
                        "class": asset2_meta["asset_class"],
                        "opportunity": asset2_meta["opportunity"]
                    },
                    "correlation": pair["correlation"],
                    "relationship": pair["relationship"],
                    "combined_score": combined_score,
                    "diversification_benefit": "high" if abs(pair["correlation"]) < 0.1 else "moderate"
                })
                
        # Sort by combined score
        cross_asset_opportunities.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return cross_asset_opportunities
        
    def calculate_portfolio_correlation(
        self,
        positions: List[Dict],
        price_data: Dict[str, List[float]]
    ) -> Dict:
        """
        Calculate overall portfolio correlation metrics
        """
        if len(positions) < 2:
            return {
                "average_correlation": 0.0,
                "max_correlation": 0.0,
                "min_correlation": 0.0,
                "diversification_score": 100.0
            }
            
        # Build correlation matrix for portfolio positions
        portfolio_assets = {
            pos["ticker"]: price_data.get(pos["ticker"], [])
            for pos in positions
            if pos["ticker"] in price_data
        }
        
        if len(portfolio_assets) < 2:
            return {
                "average_correlation": 0.0,
                "max_correlation": 0.0,
                "min_correlation": 0.0,
                "diversification_score": 100.0
            }
            
        correlation_matrix = self.calculate_correlation_matrix(portfolio_assets)
        
        # Extract correlation values (excluding diagonal)
        correlations = []
        asset_names = list(portfolio_assets.keys())
        
        for i, asset1 in enumerate(asset_names):
            for j, asset2 in enumerate(asset_names[i+1:], i+1):
                correlations.append(correlation_matrix[asset1][asset2])
                
        if not correlations:
            return {
                "average_correlation": 0.0,
                "max_correlation": 0.0,
                "min_correlation": 0.0,
                "diversification_score": 100.0
            }
            
        avg_correlation = np.mean(correlations)
        max_correlation = max(correlations)
        min_correlation = min(correlations)
        
        # Calculate diversification score (0-100, higher is better)
        # Based on average absolute correlation
        avg_abs_correlation = np.mean([abs(c) for c in correlations])
        diversification_score = (1 - avg_abs_correlation) * 100
        
        return {
            "average_correlation": avg_correlation,
            "max_correlation": max_correlation,
            "min_correlation": min_correlation,
            "diversification_score": diversification_score,
            "correlation_matrix": correlation_matrix
        }
        
    def detect_correlation_regime_change(
        self,
        historical_correlations: List[float],
        window_size: int = 20
    ) -> Optional[Dict]:
        """
        Detect significant changes in correlation patterns
        """
        if len(historical_correlations) < window_size * 2:
            return None
            
        # Calculate rolling correlation windows
        recent_window = historical_correlations[-window_size:]
        previous_window = historical_correlations[-window_size*2:-window_size]
        
        recent_avg = np.mean(recent_window)
        previous_avg = np.mean(previous_window)
        
        # Calculate change in correlation
        correlation_change = recent_avg - previous_avg
        
        # Test for statistical significance
        _, p_value = stats.ttest_ind(recent_window, previous_window)
        
        if p_value < 0.05 and abs(correlation_change) > 0.2:
            return {
                "regime_change_detected": True,
                "previous_correlation": previous_avg,
                "current_correlation": recent_avg,
                "correlation_change": correlation_change,
                "direction": "increasing" if correlation_change > 0 else "decreasing",
                "significance": p_value,
                "interpretation": self._interpret_regime_change(previous_avg, recent_avg)
            }
            
        return None
        
    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """
        Calculate percentage returns from price series
        """
        if len(prices) < 2:
            return []
            
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
                
        return returns
        
    def _classify_correlation(self, correlation: float) -> str:
        """
        Classify correlation strength and direction
        """
        abs_corr = abs(correlation)
        
        if abs_corr < 0.1:
            strength = "uncorrelated"
        elif abs_corr < 0.3:
            strength = "weakly correlated"
        elif abs_corr < 0.5:
            strength = "moderately correlated"
        elif abs_corr < 0.7:
            strength = "strongly correlated"
        else:
            strength = "very strongly correlated"
            
        if correlation > 0:
            direction = "positive"
        elif correlation < 0:
            direction = "negative"
        else:
            direction = "no"
            
        return f"{direction} {strength}" if direction != "no" else strength
        
    def _interpret_regime_change(self, previous: float, current: float) -> str:
        """
        Interpret what a correlation regime change means
        """
        prev_class = self._classify_correlation(previous)
        curr_class = self._classify_correlation(current)
        
        if abs(current) > abs(previous):
            if current > 0:
                return f"Assets becoming more synchronized (from {prev_class} to {curr_class})"
            else:
                return f"Assets moving more inversely (from {prev_class} to {curr_class})"
        else:
            return f"Assets becoming more independent (from {prev_class} to {curr_class})"
            
    def calculate_beta(
        self,
        asset_returns: List[float],
        market_returns: List[float]
    ) -> Optional[float]:
        """
        Calculate beta coefficient relative to market
        """
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 20:
            return None
            
        try:
            # Calculate covariance and market variance
            covariance = np.cov(asset_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return None
                
            beta = covariance / market_variance
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return None


# Singleton instance
correlation_analyzer = CorrelationAnalyzer()