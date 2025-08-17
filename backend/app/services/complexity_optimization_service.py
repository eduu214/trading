"""
Complexity optimization service integrating with async task processor
Handles risk-adjusted return calculations and optimal complexity selection
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from ..core.complexity_analyzer import (
    ComplexityAnalyzer, 
    ComplexityScore,
    ComplexityMetrics
)
from ..models.strategy import Strategy
from ..models.scan_result import ScanResult
from ..tasks.celery_app import celery_app
from ..services.polygon_service import PolygonService
from ..database import get_db

logger = logging.getLogger(__name__)

class RiskAdjustedCalculator:
    """Calculate risk-adjusted returns for different complexity levels"""
    
    @staticmethod
    def calculate_risk_adjusted_return(returns: pd.Series, 
                                      risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        Calculate comprehensive risk-adjusted return metrics
        
        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary of risk-adjusted metrics
        """
        daily_returns = returns.pct_change().dropna()
        
        # Annual return
        total_return = (returns.iloc[-1] / returns.iloc[0]) - 1
        days = len(returns)
        annual_return = (1 + total_return) ** (252 / days) - 1
        
        # Volatility
        volatility = daily_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar Ratio (return / max drawdown)
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio (uses downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0
        
        # Information Ratio (if benchmark provided)
        # For now, use market return assumption
        market_return = 0.08  # 8% annual market return assumption
        tracking_error = (daily_returns - market_return/252).std() * np.sqrt(252)
        information_ratio = (annual_return - market_return) / tracking_error if tracking_error > 0 else 0
        
        return {
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'information_ratio': information_ratio,
            'risk_adjusted_return': annual_return * (1 - abs(max_drawdown))  # Simple risk adjustment
        }

class ComplexityOptimizationService:
    """Main service for complexity optimization"""
    
    def __init__(self):
        self.analyzer = ComplexityAnalyzer()
        self.risk_calculator = RiskAdjustedCalculator()
        self.polygon_service = PolygonService()
        
    async def optimize_strategy_complexity(self,
                                          strategy_id: str,
                                          timeframe: str = '1D',
                                          lookback_days: int = 252,
                                          risk_preference: str = 'balanced',
                                          db: AsyncSession = None) -> Dict[str, Any]:
        """
        Optimize complexity for a given strategy
        
        Args:
            strategy_id: Strategy identifier
            timeframe: Data timeframe (1D, 1H, etc.)
            lookback_days: Days of historical data to analyze
            risk_preference: 'conservative', 'balanced', or 'aggressive'
            db: Database session
            
        Returns:
            Optimization results with recommended complexity level
        """
        try:
            # Get strategy from database
            strategy = await self._get_strategy(strategy_id, db)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Get historical data for backtesting
            market_data = await self._fetch_market_data(
                strategy.symbol,
                timeframe,
                lookback_days
            )
            
            # Test different complexity levels
            complexity_results = await self._test_complexity_levels(
                strategy,
                market_data,
                range(1, 11)  # Test levels 1-10
            )
            
            # Find optimal complexity
            optimal_level, optimal_score = self.analyzer.find_optimal_complexity(
                complexity_results['returns'],
                strategy.parameters,
                risk_preference
            )
            
            # Calculate risk-adjusted metrics for optimal level
            risk_metrics = self.risk_calculator.calculate_risk_adjusted_return(
                complexity_results['returns'][optimal_level]
            )
            
            # Store optimization results
            await self._store_optimization_results(
                strategy_id,
                optimal_level,
                optimal_score,
                risk_metrics,
                db
            )
            
            # Prepare response
            return {
                'strategy_id': strategy_id,
                'optimal_complexity_level': optimal_level,
                'current_complexity_level': strategy.complexity_level,
                'recommendation': optimal_score.recommendation,
                'confidence': optimal_score.confidence,
                'metrics': {
                    'sharpe_ratio': optimal_score.metrics.sharpe_ratio,
                    'max_drawdown': optimal_score.metrics.max_drawdown,
                    'volatility': optimal_score.metrics.volatility,
                    'win_rate': optimal_score.metrics.win_rate,
                    'profit_factor': optimal_score.metrics.profit_factor
                },
                'risk_adjusted_metrics': risk_metrics,
                'performance_improvement': self._calculate_improvement(
                    strategy.complexity_level,
                    optimal_level,
                    complexity_results
                ),
                'all_levels_comparison': self._format_comparison(complexity_results),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Complexity optimization failed: {str(e)}")
            raise
    
    async def _get_strategy(self, strategy_id: str, db: AsyncSession) -> Optional[Strategy]:
        """Fetch strategy from database"""
        result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        return result.scalar_one_or_none()
    
    async def _fetch_market_data(self,
                                symbol: str,
                                timeframe: str,
                                lookback_days: int) -> pd.DataFrame:
        """Fetch historical market data for backtesting"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get data from Polygon
        bars = await self.polygon_service.get_aggregates(
            symbol,
            1,
            timeframe,
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
    
    async def _test_complexity_levels(self,
                                     strategy: Strategy,
                                     market_data: pd.DataFrame,
                                     complexity_levels: range) -> Dict[str, Any]:
        """Test strategy at different complexity levels"""
        results = {
            'returns': {},
            'metrics': {},
            'parameters': {}
        }
        
        for level in complexity_levels:
            # Adjust strategy parameters for complexity level
            adjusted_params = self._adjust_parameters_for_complexity(
                strategy.parameters,
                level
            )
            
            # Simulate strategy with adjusted parameters
            returns = await self._simulate_strategy(
                market_data,
                adjusted_params,
                level
            )
            
            # Store results
            results['returns'][level] = returns
            results['parameters'][level] = adjusted_params
            
            # Calculate metrics
            metrics = self.risk_calculator.calculate_risk_adjusted_return(returns)
            results['metrics'][level] = metrics
        
        return results
    
    def _adjust_parameters_for_complexity(self,
                                         base_params: Dict,
                                         complexity_level: int) -> Dict:
        """Adjust strategy parameters based on complexity level"""
        adjusted = base_params.copy()
        
        # Complexity level 1-3: Simple strategies
        if complexity_level <= 3:
            adjusted['indicators'] = base_params.get('indicators', [])[:complexity_level]
            adjusted['rules'] = base_params.get('rules', [])[:1]
            adjusted['risk_management'] = {'stop_loss': 0.02, 'take_profit': 0.04}
            
        # Complexity level 4-6: Moderate strategies
        elif complexity_level <= 6:
            adjusted['indicators'] = base_params.get('indicators', [])[:complexity_level]
            adjusted['rules'] = base_params.get('rules', [])[:2]
            adjusted['timeframes'] = min(complexity_level - 3, len(base_params.get('timeframes', [1])))
            adjusted['risk_management'] = {
                'stop_loss': 0.015,
                'take_profit': 0.05,
                'position_sizing': 'kelly'
            }
            
        # Complexity level 7-10: Advanced strategies
        else:
            adjusted['indicators'] = base_params.get('indicators', [])
            adjusted['rules'] = base_params.get('rules', [])
            adjusted['ml_models'] = complexity_level - 6  # Number of ML models
            adjusted['ensemble_method'] = 'voting' if complexity_level < 9 else 'stacking'
            adjusted['risk_management'] = {
                'stop_loss': 'dynamic',
                'take_profit': 'dynamic',
                'position_sizing': 'optimal_f',
                'risk_parity': True
            }
        
        return adjusted
    
    async def _simulate_strategy(self,
                                market_data: pd.DataFrame,
                                parameters: Dict,
                                complexity_level: int) -> pd.Series:
        """
        Simulate strategy execution with given parameters
        This is a simplified simulation - real implementation would use vectorbt
        """
        # Initialize with market close prices
        prices = market_data['close']
        returns = pd.Series(index=prices.index, dtype=float)
        
        # Simple simulation based on complexity level
        if complexity_level <= 3:
            # Simple moving average crossover
            sma_short = prices.rolling(window=10).mean()
            sma_long = prices.rolling(window=30).mean()
            
            signals = (sma_short > sma_long).astype(int)
            signals = signals.diff()
            
            # Calculate returns
            position = 0
            for i in range(1, len(prices)):
                if signals.iloc[i] == 1:  # Buy signal
                    position = 1
                elif signals.iloc[i] == -1:  # Sell signal
                    position = 0
                
                if position == 1:
                    returns.iloc[i] = prices.iloc[i] / prices.iloc[i-1] - 1
                else:
                    returns.iloc[i] = 0
                    
        elif complexity_level <= 6:
            # More complex strategy with multiple indicators
            # RSI + MACD combination
            rsi = self._calculate_rsi(prices)
            macd_signal = self._calculate_macd_signal(prices)
            
            # Generate signals
            buy_signal = (rsi < 30) & (macd_signal > 0)
            sell_signal = (rsi > 70) | (macd_signal < 0)
            
            position = 0
            for i in range(1, len(prices)):
                if buy_signal.iloc[i]:
                    position = 1
                elif sell_signal.iloc[i]:
                    position = 0
                
                if position == 1:
                    returns.iloc[i] = prices.iloc[i] / prices.iloc[i-1] - 1
                else:
                    returns.iloc[i] = 0
                    
        else:
            # Advanced ML-based strategy (simplified)
            # Use price patterns and technical indicators
            features = self._extract_features(market_data)
            predictions = self._ml_predict(features, complexity_level)
            
            for i in range(1, len(prices)):
                if predictions[i] > 0.6:  # High confidence buy
                    returns.iloc[i] = prices.iloc[i] / prices.iloc[i-1] - 1
                elif predictions[i] < 0.4:  # High confidence sell
                    returns.iloc[i] = 0
                else:
                    returns.iloc[i] = returns.iloc[i-1] if i > 0 else 0
        
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
    
    def _calculate_macd_signal(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD signal"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd - signal
    
    def _extract_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """Extract features for ML model"""
        features = []
        
        # Price-based features
        features.append(market_data['close'].pct_change())
        features.append((market_data['high'] - market_data['low']) / market_data['close'])
        features.append((market_data['close'] - market_data['open']) / market_data['open'])
        
        # Volume features
        features.append(market_data['volume'].pct_change())
        
        # Technical indicators
        features.append(self._calculate_rsi(market_data['close']))
        features.append(self._calculate_macd_signal(market_data['close']))
        
        # Combine features
        feature_matrix = pd.DataFrame(features).T.fillna(0)
        return feature_matrix.values
    
    def _ml_predict(self, features: np.ndarray, complexity_level: int) -> np.ndarray:
        """
        Simplified ML prediction
        In production, this would use trained models
        """
        # Simple prediction based on feature patterns
        predictions = np.zeros(len(features))
        
        for i in range(1, len(features)):
            # Use different "models" based on complexity
            if complexity_level == 7:
                # Single model
                predictions[i] = 0.5 + 0.1 * np.mean(features[i])
            elif complexity_level == 8:
                # Ensemble of 2 models
                pred1 = 0.5 + 0.1 * np.mean(features[i])
                pred2 = 0.5 + 0.05 * np.std(features[i])
                predictions[i] = (pred1 + pred2) / 2
            else:
                # Multiple models with stacking
                preds = []
                for j in range(complexity_level - 6):
                    preds.append(0.5 + (0.1 / (j + 1)) * np.mean(features[i]))
                predictions[i] = np.mean(preds)
        
        # Normalize to [0, 1]
        predictions = np.clip(predictions, 0, 1)
        return predictions
    
    def _calculate_improvement(self,
                              current_level: int,
                              optimal_level: int,
                              results: Dict) -> Dict[str, float]:
        """Calculate performance improvement from optimization"""
        if current_level not in results['metrics'] or optimal_level not in results['metrics']:
            return {}
        
        current_metrics = results['metrics'][current_level]
        optimal_metrics = results['metrics'][optimal_level]
        
        return {
            'sharpe_improvement': optimal_metrics['sharpe_ratio'] - current_metrics['sharpe_ratio'],
            'return_improvement': optimal_metrics['annual_return'] - current_metrics['annual_return'],
            'drawdown_improvement': optimal_metrics['max_drawdown'] - current_metrics['max_drawdown'],
            'risk_adjusted_improvement': optimal_metrics['risk_adjusted_return'] - current_metrics['risk_adjusted_return']
        }
    
    def _format_comparison(self, results: Dict) -> List[Dict]:
        """Format comparison of all complexity levels"""
        comparison = []
        
        for level in results['returns'].keys():
            metrics = results['metrics'][level]
            comparison.append({
                'complexity_level': level,
                'annual_return': round(metrics['annual_return'], 4),
                'sharpe_ratio': round(metrics['sharpe_ratio'], 2),
                'max_drawdown': round(metrics['max_drawdown'], 4),
                'volatility': round(metrics['volatility'], 4),
                'risk_adjusted_return': round(metrics['risk_adjusted_return'], 4)
            })
        
        return sorted(comparison, key=lambda x: x['risk_adjusted_return'], reverse=True)
    
    async def _store_optimization_results(self,
                                         strategy_id: str,
                                         optimal_level: int,
                                         score: ComplexityScore,
                                         risk_metrics: Dict,
                                         db: AsyncSession):
        """Store optimization results in database"""
        # Update strategy with optimal complexity
        strategy = await self._get_strategy(strategy_id, db)
        if strategy:
            strategy.complexity_level = optimal_level
            strategy.complexity_score = score.overall_score
            strategy.last_optimized = datetime.utcnow()
            strategy.optimization_metrics = {
                'score': score.to_dict(),
                'risk_metrics': risk_metrics
            }
            
            await db.commit()

# Celery task for async complexity optimization
@celery_app.task(name='optimize_strategy_complexity')
def optimize_strategy_complexity_task(strategy_id: str,
                                      timeframe: str = '1D',
                                      lookback_days: int = 252,
                                      risk_preference: str = 'balanced'):
    """
    Celery task for async complexity optimization
    """
    service = ComplexityOptimizationService()
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            service.optimize_strategy_complexity(
                strategy_id,
                timeframe,
                lookback_days,
                risk_preference
            )
        )
        return result
    finally:
        loop.close()