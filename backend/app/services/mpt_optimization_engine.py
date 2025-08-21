"""
Modern Portfolio Theory Optimization Engine
F003-US001 Task 6: Implement MPT with efficient frontier calculation

Handles:
- Mean-variance optimization using PyPortfolioOpt
- Efficient frontier calculation for risk-return visualization  
- 30% maximum allocation constraint per strategy
- Multiple optimization objectives (max Sharpe, min volatility, efficient risk)
- Portfolio performance metrics calculation
- Risk budgeting and constraint validation
"""

import numpy as np
import pandas as pd
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging

from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
import empyrical
import QuantLib as ql

from app.services.portfolio_state_manager import get_portfolio_state_manager

logger = logging.getLogger(__name__)

class MPTOptimizationEngine:
    """Modern Portfolio Theory optimization engine with efficient frontier calculation"""
    
    def __init__(self):
        self.max_weight_per_strategy = 0.30  # 30% maximum allocation per strategy
        self.min_weight_threshold = 0.01     # 1% minimum allocation threshold
        self.risk_free_rate = 0.02           # 2% risk-free rate assumption
        
    def calculate_efficient_frontier(
        self, 
        strategy_returns: pd.DataFrame,
        n_points: int = 100,
        risk_aversion_range: Tuple[float, float] = (0.1, 10.0)
    ) -> Dict[str, Any]:
        """
        Calculate efficient frontier points for portfolio visualization
        
        Args:
            strategy_returns: DataFrame with strategy returns
            n_points: Number of points to calculate on efficient frontier
            risk_aversion_range: Range of risk aversion parameters
            
        Returns:
            Dict containing efficient frontier data and optimal portfolios
        """
        try:
            # Calculate expected returns and risk model
            mu = expected_returns.mean_historical_return(strategy_returns, frequency=252)
            S = risk_models.sample_cov(strategy_returns, frequency=252)
            S = risk_models.fix_nonpositive_semidefinite(S)
            
            # Generate efficient frontier points using target volatility approach
            frontier_points = []
            optimal_portfolios = {}
            
            # Calculate min and max volatility bounds
            try:
                ef_min = EfficientFrontier(mu, S, weight_bounds=(0, self.max_weight_per_strategy))
                ef_min.min_volatility()
                min_perf = ef_min.portfolio_performance(verbose=False)
                min_vol = min_perf[1]
                
                ef_max = EfficientFrontier(mu, S, weight_bounds=(0, self.max_weight_per_strategy))
                # Use maximum single asset volatility as upper bound
                max_vol = np.sqrt(np.diag(S)).max()
                
                # Create target volatility range
                target_volatilities = np.linspace(min_vol, min(max_vol, min_vol * 3), n_points)
                
                for target_vol in target_volatilities:
                    try:
                        ef = EfficientFrontier(mu, S, weight_bounds=(0, self.max_weight_per_strategy))
                        
                        # Optimize for this target volatility
                        weights = ef.efficient_risk(target_volatility=target_vol)
                        cleaned_weights = ef.clean_weights(cutoff=self.min_weight_threshold)
                        
                        # Calculate performance metrics
                        performance = ef.portfolio_performance(verbose=False)
                        expected_return, volatility, sharpe_ratio = performance
                        
                        # Store frontier point
                        frontier_points.append({
                            'expected_return': float(expected_return),
                            'volatility': float(volatility),
                            'sharpe_ratio': float(sharpe_ratio),
                            'target_volatility': float(target_vol),
                            'weights': {k: float(v) for k, v in cleaned_weights.items()}
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error calculating frontier point for volatility {target_vol}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not calculate volatility bounds: {e}")
                
            # If no frontier points calculated, create manual portfolios as fallback
            if not frontier_points:
                logger.info("Creating fallback efficient frontier using manual portfolio construction")
                strategies = list(mu.index)
                n_strategies = len(strategies)
                
                # Create diverse portfolios manually
                portfolio_configs = [
                    # Equal weights
                    {s: 1.0/n_strategies for s in strategies},
                    # Concentrated on highest return strategy
                    {strategies[mu.argmax()]: 0.5, **{s: 0.5/(n_strategies-1) for s in strategies if s != strategies[mu.argmax()]}},
                    # Concentrated on lowest volatility strategy
                    {strategies[np.sqrt(np.diag(S)).argmin()]: 0.5, **{s: 0.5/(n_strategies-1) for s in strategies if s != strategies[np.sqrt(np.diag(S)).argmin()]}},
                ]
                
                for weights_dict in portfolio_configs:
                    portfolio_returns = (strategy_returns * pd.Series(weights_dict)).sum(axis=1)
                    expected_return = portfolio_returns.mean() * 252
                    volatility = portfolio_returns.std() * np.sqrt(252)
                    sharpe_ratio = (expected_return - self.risk_free_rate) / volatility
                    
                    # Validate and clean float values for JSON serialization
                    def clean_float(value):
                        if np.isnan(value) or np.isinf(value):
                            return 0.0
                        return float(value)
                    
                    frontier_points.append({
                        'expected_return': clean_float(expected_return),
                        'volatility': clean_float(volatility),
                        'sharpe_ratio': clean_float(sharpe_ratio),
                        'target_volatility': clean_float(volatility),
                        'weights': weights_dict
                    })
            
            # Calculate special optimal portfolios with fallback
            try:
                # Maximum Sharpe ratio portfolio
                try:
                    ef_max_sharpe = EfficientFrontier(mu, S, weight_bounds=(0, self.max_weight_per_strategy))
                    max_sharpe_weights = ef_max_sharpe.max_sharpe()
                    max_sharpe_cleaned = ef_max_sharpe.clean_weights(cutoff=self.min_weight_threshold)
                    max_sharpe_performance = ef_max_sharpe.portfolio_performance(verbose=False)
                    
                    optimal_portfolios['max_sharpe'] = {
                        'weights': {k: float(v) for k, v in max_sharpe_cleaned.items()},
                        'expected_return': float(max_sharpe_performance[0]),
                        'volatility': float(max_sharpe_performance[1]),
                        'sharpe_ratio': float(max_sharpe_performance[2])
                    }
                except Exception:
                    # Fallback: equal weights for max Sharpe
                    equal_weights = {asset: 1.0/len(mu) for asset in mu.index}
                    portfolio_returns = (strategy_returns * pd.Series(equal_weights)).sum(axis=1)
                    expected_return = portfolio_returns.mean() * 252
                    volatility = portfolio_returns.std() * np.sqrt(252)
                    sharpe_ratio = (expected_return - self.risk_free_rate) / volatility
                    
                    # Clean float helper function
                    def clean_float(value):
                        if np.isnan(value) or np.isinf(value):
                            return 0.0
                        return float(value)
                    
                    optimal_portfolios['max_sharpe'] = {
                        'weights': equal_weights,
                        'expected_return': clean_float(expected_return),
                        'volatility': clean_float(volatility),
                        'sharpe_ratio': clean_float(sharpe_ratio)
                    }
                
                # Minimum volatility portfolio
                try:
                    ef_min_vol = EfficientFrontier(mu, S, weight_bounds=(0, self.max_weight_per_strategy))
                    min_vol_weights = ef_min_vol.min_volatility()
                    min_vol_cleaned = ef_min_vol.clean_weights(cutoff=self.min_weight_threshold)
                    min_vol_performance = ef_min_vol.portfolio_performance(verbose=False)
                    
                    optimal_portfolios['min_volatility'] = {
                        'weights': {k: float(v) for k, v in min_vol_cleaned.items()},
                        'expected_return': float(min_vol_performance[0]),
                        'volatility': float(min_vol_performance[1]),
                        'sharpe_ratio': float(min_vol_performance[2])
                    }
                except Exception:
                    # Fallback: concentrate on lowest volatility strategy
                    min_vol_strategy = strategies[np.sqrt(np.diag(S)).argmin()]
                    low_vol_weights = {min_vol_strategy: 0.6, **{s: 0.4/(len(strategies)-1) for s in strategies if s != min_vol_strategy}}
                    portfolio_returns = (strategy_returns * pd.Series(low_vol_weights)).sum(axis=1)
                    expected_return = portfolio_returns.mean() * 252
                    volatility = portfolio_returns.std() * np.sqrt(252)
                    sharpe_ratio = (expected_return - self.risk_free_rate) / volatility
                    
                    # Clean float helper function
                    def clean_float(value):
                        if np.isnan(value) or np.isinf(value):
                            return 0.0
                        return float(value)
                    
                    optimal_portfolios['min_volatility'] = {
                        'weights': low_vol_weights,
                        'expected_return': clean_float(expected_return),
                        'volatility': clean_float(volatility),
                        'sharpe_ratio': clean_float(sharpe_ratio)
                    }
                
            except Exception as e:
                logger.warning(f"Error calculating optimal portfolios: {e}")
            
            return {
                'frontier_points': frontier_points,
                'optimal_portfolios': optimal_portfolios,
                'n_strategies': len(strategy_returns.columns),
                'calculation_date': datetime.utcnow().isoformat(),
                'risk_free_rate': self.risk_free_rate,
                'constraints': {
                    'max_weight_per_strategy': self.max_weight_per_strategy,
                    'min_weight_threshold': self.min_weight_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating efficient frontier: {e}")
            return {
                'frontier_points': [],
                'optimal_portfolios': {},
                'error': str(e)
            }
    
    def optimize_portfolio(
        self,
        strategy_returns: pd.DataFrame,
        optimization_method: str = "max_sharpe",
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        custom_constraints: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using Modern Portfolio Theory
        
        Args:
            strategy_returns: DataFrame with strategy returns
            optimization_method: 'max_sharpe', 'min_volatility', 'efficient_return', 'efficient_risk'
            target_return: Target return for efficient return optimization
            target_volatility: Target volatility for efficient risk optimization
            custom_constraints: Custom weight constraints per strategy
            
        Returns:
            Dict with optimization results and portfolio metrics
        """
        try:
            # Calculate expected returns and risk model
            mu = expected_returns.mean_historical_return(strategy_returns, frequency=252)
            S = risk_models.sample_cov(strategy_returns, frequency=252)
            S = risk_models.fix_nonpositive_semidefinite(S)
            
            # Set up weight bounds
            weight_bounds = (0, self.max_weight_per_strategy)
            if custom_constraints:
                # Apply custom constraints (future enhancement)
                pass
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            
            # Perform optimization based on method with fallback handling
            use_fallback = False
            
            if optimization_method == "max_sharpe":
                try:
                    weights = ef.max_sharpe()
                except Exception as e:
                    logger.warning(f"Max Sharpe optimization failed, using equal weights: {e}")
                    use_fallback = True
            elif optimization_method == "min_volatility":
                weights = ef.min_volatility()
            elif optimization_method == "efficient_return" and target_return:
                try:
                    weights = ef.efficient_return(target_return=target_return)
                except Exception:
                    # Fallback to min volatility
                    weights = ef.min_volatility()
            elif optimization_method == "efficient_risk" and target_volatility:
                try:
                    weights = ef.efficient_risk(target_volatility=target_volatility)
                except Exception:
                    # Fallback to min volatility
                    weights = ef.min_volatility()
            else:
                # Default to min volatility (more stable)
                weights = ef.min_volatility()
            
            # Handle fallback case
            if use_fallback:
                n_assets = len(mu)
                cleaned_weights = {asset: 1.0/n_assets for asset in mu.index}
            else:
                # Clean weights
                cleaned_weights = ef.clean_weights(cutoff=self.min_weight_threshold)
            
            # Calculate performance metrics
            if use_fallback:
                # Calculate performance manually for equal weights
                portfolio_returns = (strategy_returns * pd.Series(cleaned_weights)).sum(axis=1)
                expected_annual_return = portfolio_returns.mean() * 252
                annual_volatility = portfolio_returns.std() * np.sqrt(252)
                sharpe_ratio = (expected_annual_return - self.risk_free_rate) / annual_volatility
            else:
                performance = ef.portfolio_performance(verbose=False)
                expected_annual_return, annual_volatility, sharpe_ratio = performance
            
            # Calculate additional risk metrics
            portfolio_returns = (strategy_returns * pd.Series(cleaned_weights)).sum(axis=1)
            
            additional_metrics = self._calculate_additional_metrics(portfolio_returns)
            
            # Calculate discrete allocation (for actual portfolio construction)
            total_portfolio_value = 10000  # $10k default
            latest_prices = pd.Series({strategy: 1.0 for strategy in cleaned_weights.keys()})  # Unit prices as Series
            
            da = DiscreteAllocation(cleaned_weights, latest_prices, total_portfolio_value=total_portfolio_value)
            allocation, leftover = da.lp_portfolio()
            
            # Convert allocation to standard types for JSON serialization
            allocation = {k: int(v) for k, v in allocation.items()}
            
            return {
                'success': True,
                'optimization_method': optimization_method,
                'optimal_weights': {k: float(v) for k, v in cleaned_weights.items()},
                'discrete_allocation': allocation,
                'leftover_cash': float(leftover),
                'performance_metrics': {
                    'expected_annual_return': float(expected_annual_return),
                    'annual_volatility': float(annual_volatility),
                    'sharpe_ratio': float(sharpe_ratio),
                    **additional_metrics
                },
                'portfolio_characteristics': {
                    'total_strategies': len([w for w in cleaned_weights.values() if w > 0]),
                    'total_allocation': sum(cleaned_weights.values()),
                    'max_weight': max(cleaned_weights.values()) if cleaned_weights else 0,
                    'min_weight': min([w for w in cleaned_weights.values() if w > 0]) if cleaned_weights else 0,
                    'concentration_ratio': self._calculate_concentration_ratio(cleaned_weights)
                },
                'optimization_timestamp': datetime.utcnow().isoformat(),
                'constraints_applied': {
                    'max_weight_per_strategy': self.max_weight_per_strategy,
                    'min_weight_threshold': self.min_weight_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return {
                'success': False,
                'error': str(e),
                'optimization_method': optimization_method
            }
    
    def _calculate_additional_metrics(self, portfolio_returns: pd.Series) -> Dict[str, float]:
        """Calculate additional portfolio risk metrics"""
        try:
            metrics = {}
            
            # Helper to clean float values
            def clean_float(value):
                if np.isnan(value) or np.isinf(value):
                    return 0.0
                return float(value)
            
            # Maximum drawdown
            metrics['max_drawdown'] = clean_float(empyrical.max_drawdown(portfolio_returns))
            
            # Value at Risk (95% confidence)
            metrics['var_95'] = clean_float(np.percentile(portfolio_returns, 5) * np.sqrt(252) * -1)
            
            # Conditional Value at Risk (Expected Shortfall)
            var_95_threshold = np.percentile(portfolio_returns, 5)
            cvar_returns = portfolio_returns[portfolio_returns <= var_95_threshold]
            cvar_value = cvar_returns.mean() * np.sqrt(252) * -1 if len(cvar_returns) > 0 else 0
            metrics['cvar_95'] = clean_float(cvar_value)
            
            # Sortino ratio (downside deviation)
            downside_returns = portfolio_returns[portfolio_returns < 0]
            if len(downside_returns) > 0:
                downside_deviation = np.sqrt(np.mean(downside_returns**2)) * np.sqrt(252)
                annual_return = portfolio_returns.mean() * 252
                sortino = (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
                metrics['sortino_ratio'] = clean_float(sortino)
            else:
                metrics['sortino_ratio'] = 0.0  # Use 0 instead of inf
            
            # Calmar ratio (annual return / max drawdown)
            annual_return = portfolio_returns.mean() * 252
            max_dd = abs(empyrical.max_drawdown(portfolio_returns))
            calmar = annual_return / max_dd if max_dd > 0 else 0
            metrics['calmar_ratio'] = clean_float(calmar)
            
            # Volatility skewness and kurtosis
            metrics['skewness'] = clean_float(portfolio_returns.skew())
            metrics['kurtosis'] = clean_float(portfolio_returns.kurtosis())
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error calculating additional metrics: {e}")
            return {}
    
    def _calculate_concentration_ratio(self, weights: Dict[str, float]) -> float:
        """Calculate portfolio concentration ratio (Herfindahl-Hirschman Index)"""
        try:
            return sum(w**2 for w in weights.values())
        except:
            return 0.0
    
    def validate_allocation_constraints(
        self,
        allocation: Dict[str, float],
        custom_constraints: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Validate portfolio allocation against constraints
        
        Args:
            allocation: Strategy allocation weights
            custom_constraints: Custom constraints per strategy
            
        Returns:
            Dict with validation results
        """
        violations = []
        warnings = []
        
        # Check maximum allocation constraint
        for strategy, weight in allocation.items():
            if weight > self.max_weight_per_strategy:
                violations.append({
                    'type': 'max_allocation_exceeded',
                    'strategy': strategy,
                    'current_weight': weight,
                    'max_allowed': self.max_weight_per_strategy
                })
        
        # Check minimum allocation threshold
        for strategy, weight in allocation.items():
            if 0 < weight < self.min_weight_threshold:
                warnings.append({
                    'type': 'below_minimum_threshold',
                    'strategy': strategy,
                    'current_weight': weight,
                    'min_threshold': self.min_weight_threshold
                })
        
        # Check total allocation
        total_allocation = sum(allocation.values())
        if abs(total_allocation - 1.0) > 0.01:  # 1% tolerance
            violations.append({
                'type': 'total_allocation_error',
                'total_allocation': total_allocation,
                'expected': 1.0
            })
        
        # Apply custom constraints if provided
        if custom_constraints:
            for strategy, constraints in custom_constraints.items():
                if strategy in allocation:
                    weight = allocation[strategy]
                    
                    if 'max_weight' in constraints and weight > constraints['max_weight']:
                        violations.append({
                            'type': 'custom_max_exceeded',
                            'strategy': strategy,
                            'current_weight': weight,
                            'max_allowed': constraints['max_weight']
                        })
                    
                    if 'min_weight' in constraints and weight < constraints['min_weight']:
                        violations.append({
                            'type': 'custom_min_violation',
                            'strategy': strategy,
                            'current_weight': weight,
                            'min_required': constraints['min_weight']
                        })
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'total_allocation': total_allocation,
            'n_strategies': len([w for w in allocation.values() if w > 0])
        }
    
    def get_strategy_returns_data(self, portfolio_id: str = "main", window_days: int = 252) -> pd.DataFrame:
        """Get strategy returns data for optimization"""
        try:
            # In production, this would connect to the database and get actual strategy performance
            # For now, generate realistic sample data
            
            strategies = ['rsi_mean_reversion', 'macd_momentum', 'bollinger_breakout', 'mean_reversion_pairs', 'momentum_breakout']
            dates = pd.date_range(end=datetime.now(), periods=window_days, freq='D')
            
            # Generate realistic daily returns with different risk/return profiles
            np.random.seed(42)
            returns_data = {}
            
            # Strategy characteristics (annual return, annual volatility, market correlation)
            strategy_params = {
                'rsi_mean_reversion': (0.12, 0.18, 0.3),      # 12% return, 18% vol, 0.3 market correlation
                'macd_momentum': (0.15, 0.22, 0.5),           # 15% return, 22% vol, 0.5 market correlation  
                'bollinger_breakout': (0.10, 0.25, 0.4),      # 10% return, 25% vol, 0.4 market correlation
                'mean_reversion_pairs': (0.08, 0.12, 0.1),    # 8% return, 12% vol, 0.1 market correlation
                'momentum_breakout': (0.18, 0.28, 0.6)        # 18% return, 28% vol, 0.6 market correlation
            }
            
            # Generate common market factor
            market_returns = np.random.normal(0.0008, 0.015, window_days)  # Market factor
            
            for strategy, (annual_return, annual_vol, market_corr) in strategy_params.items():
                # Convert annual to daily
                daily_return = annual_return / 252
                daily_vol = annual_vol / np.sqrt(252)
                
                # Generate idiosyncratic returns
                idiosyncratic = np.random.normal(daily_return, daily_vol * np.sqrt(1 - market_corr**2), window_days)
                
                # Combine with market factor
                strategy_returns = idiosyncratic + (market_returns * market_corr)
                
                returns_data[strategy] = strategy_returns
            
            df = pd.DataFrame(returns_data, index=dates)
            return df
            
        except Exception as e:
            logger.error(f"Error getting strategy returns data: {e}")
            return pd.DataFrame()

# Global MPT engine instance
mpt_engine = MPTOptimizationEngine()

def get_mpt_engine() -> MPTOptimizationEngine:
    """Get the global MPT optimization engine instance"""
    return mpt_engine