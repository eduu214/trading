"""
MACD Strategy Calculator
Implements MACD signal line crossover logic for strategy signals
Part of F002-US001 Slice 2: Alternative Strategy Types
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from loguru import logger
from datetime import datetime
import asyncio

from app.services.technical_indicators import TechnicalIndicatorService


class MACDCalculator:
    """Calculate MACD strategy signals with signal line crossover logic"""
    
    def __init__(self):
        """Initialize MACD calculator with technical indicator service"""
        self.indicator_service = TechnicalIndicatorService()
    
    async def generate_signals(
        self,
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        min_signal_strength: float = 0.001
    ) -> Dict[str, pd.Series]:
        """
        Generate MACD buy/sell signals based on signal line crossover
        
        Args:
            prices: Series of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            min_signal_strength: Minimum MACD value for signal strength (default 0.001)
            
        Returns:
            Dictionary containing:
            - 'macd': MACD line values
            - 'signal': Signal line values
            - 'histogram': MACD histogram
            - 'buy_signals': Buy signal indicators (1 for buy, 0 otherwise)
            - 'sell_signals': Sell signal indicators (-1 for sell, 0 otherwise)
            - 'signal_strength': Signal strength based on MACD histogram
        """
        try:
            logger.info(f"Generating MACD signals for {len(prices)} price points")
            
            # Calculate MACD components
            macd_data = await self.indicator_service.calculate_macd(
                prices, fast_period, slow_period, signal_period
            )
            
            if macd_data['macd'].empty:
                logger.warning("No MACD data calculated - insufficient price data")
                return self._empty_signals(prices.index)
            
            macd_line = macd_data['macd']
            signal_line = macd_data['signal']
            histogram = macd_data['histogram']
            
            # Generate crossover signals
            buy_signals, sell_signals = self._detect_crossovers(
                macd_line, signal_line, min_signal_strength
            )
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(histogram)
            
            # Count generated signals
            buy_count = buy_signals.sum()
            sell_count = abs(sell_signals.sum())
            logger.info(f"Generated {buy_count} buy signals and {sell_count} sell signals")
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'signal_strength': signal_strength
            }
            
        except Exception as e:
            logger.error(f"Error generating MACD signals: {e}")
            return self._empty_signals(prices.index)
    
    def _detect_crossovers(
        self,
        macd_line: pd.Series,
        signal_line: pd.Series,
        min_signal_strength: float
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Detect MACD signal line crossovers for buy/sell signals
        
        Args:
            macd_line: MACD line values
            signal_line: Signal line values
            min_signal_strength: Minimum signal strength threshold
            
        Returns:
            Tuple of (buy_signals, sell_signals) Series
        """
        try:
            # Calculate crossover differences
            macd_diff = macd_line - signal_line
            
            # Detect crossovers by finding sign changes
            crossovers = np.diff(np.sign(macd_diff))
            
            # Pad crossovers array to match original length
            crossovers = np.concatenate([[0], crossovers])
            
            # Initialize signal arrays
            buy_signals = pd.Series(0, index=macd_line.index, dtype=int)
            sell_signals = pd.Series(0, index=macd_line.index, dtype=int)
            
            # Generate buy signals (MACD crosses above signal line)
            buy_mask = (crossovers > 0) & (abs(macd_diff) >= min_signal_strength)
            buy_signals[buy_mask] = 1
            
            # Generate sell signals (MACD crosses below signal line)
            sell_mask = (crossovers < 0) & (abs(macd_diff) >= min_signal_strength)
            sell_signals[sell_mask] = -1
            
            return buy_signals, sell_signals
            
        except Exception as e:
            logger.error(f"Error detecting MACD crossovers: {e}")
            empty_series = pd.Series(0, index=macd_line.index, dtype=int)
            return empty_series, empty_series
    
    def _calculate_signal_strength(self, histogram: pd.Series) -> pd.Series:
        """
        Calculate signal strength based on MACD histogram magnitude
        
        Args:
            histogram: MACD histogram values
            
        Returns:
            Series of signal strength values (0-1 scale)
        """
        try:
            # Use absolute histogram values for strength
            abs_histogram = abs(histogram)
            
            # Normalize to 0-1 scale using rolling window
            window_size = min(20, len(abs_histogram))
            if window_size < 5:
                return pd.Series(0.5, index=histogram.index)
            
            rolling_max = abs_histogram.rolling(window=window_size, min_periods=1).max()
            
            # Avoid division by zero
            strength = abs_histogram / (rolling_max + 1e-8)
            
            # Cap at 1.0
            strength = np.minimum(strength, 1.0)
            
            return strength
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return pd.Series(0.5, index=histogram.index)
    
    def _empty_signals(self, index: pd.Index) -> Dict[str, pd.Series]:
        """Return empty signal structure for error cases"""
        return {
            'macd': pd.Series(dtype=float, index=index),
            'signal': pd.Series(dtype=float, index=index),
            'histogram': pd.Series(dtype=float, index=index),
            'buy_signals': pd.Series(0, index=index, dtype=int),
            'sell_signals': pd.Series(0, index=index, dtype=int),
            'signal_strength': pd.Series(0.0, index=index)
        }
    
    async def validate_parameters(
        self,
        fast_period: int,
        slow_period: int,
        signal_period: int
    ) -> Dict[str, bool]:
        """
        Validate MACD parameter configuration
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Dictionary with validation results and error messages
        """
        validation = {
            'valid': True,
            'errors': []
        }
        
        # Check period constraints
        if fast_period <= 0 or fast_period > 50:
            validation['valid'] = False
            validation['errors'].append(f"Fast period must be 1-50, got {fast_period}")
        
        if slow_period <= 0 or slow_period > 100:
            validation['valid'] = False
            validation['errors'].append(f"Slow period must be 1-100, got {slow_period}")
        
        if signal_period <= 0 or signal_period > 50:
            validation['valid'] = False
            validation['errors'].append(f"Signal period must be 1-50, got {signal_period}")
        
        # Check logical constraints
        if fast_period >= slow_period:
            validation['valid'] = False
            validation['errors'].append("Fast period must be less than slow period")
        
        logger.info(f"MACD parameter validation: {validation}")
        return validation
    
    async def get_strategy_description(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> str:
        """
        Get human-readable strategy description
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Strategy description string
        """
        return (
            f"MACD Strategy: "
            f"Fast EMA({fast_period}) - Slow EMA({slow_period}) with Signal({signal_period}). "
            f"Buy when MACD crosses above signal line, sell when crosses below."
        )