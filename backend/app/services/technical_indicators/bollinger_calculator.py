"""
Bollinger Bands Strategy Calculator
Implements Bollinger Bands mean reversion strategy with configurable standard deviation bands
Part of F002-US001 Slice 2: Alternative Strategy Types
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from loguru import logger
from datetime import datetime
import asyncio

from app.services.technical_indicators import TechnicalIndicatorService


class BollingerCalculator:
    """Calculate Bollinger Bands strategy signals with mean reversion logic"""
    
    def __init__(self):
        """Initialize Bollinger Bands calculator with technical indicator service"""
        self.indicator_service = TechnicalIndicatorService()
    
    async def generate_signals(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
        entry_threshold: float = 0.02,  # 2% from band for signal
        exit_threshold: float = 0.1     # 10% return to middle for exit
    ) -> Dict[str, pd.Series]:
        """
        Generate Bollinger Bands buy/sell signals based on mean reversion
        
        Args:
            prices: Series of closing prices
            period: Moving average period (default 20)
            std_dev: Number of standard deviations (default 2.0)
            entry_threshold: Distance from band as % of price for signal entry
            exit_threshold: Distance from middle band as % for signal exit
            
        Returns:
            Dictionary containing:
            - 'upper': Upper Bollinger Band
            - 'middle': Middle Bollinger Band (SMA)
            - 'lower': Lower Bollinger Band
            - 'buy_signals': Buy signal indicators (1 for buy, 0 otherwise)
            - 'sell_signals': Sell signal indicators (-1 for sell, 0 otherwise)
            - 'squeeze': Bollinger Band squeeze indicator (low volatility)
            - 'band_width': Band width normalized to middle band
        """
        try:
            logger.info(f"Generating Bollinger Bands signals for {len(prices)} price points")
            
            # Calculate Bollinger Bands
            bb_data = await self.indicator_service.calculate_bollinger_bands(
                prices, period, std_dev
            )
            
            if bb_data['upper'].empty:
                logger.warning("No Bollinger Bands data calculated - insufficient price data")
                return self._empty_signals(prices.index)
            
            upper_band = bb_data['upper']
            middle_band = bb_data['middle']
            lower_band = bb_data['lower']
            
            # Generate mean reversion signals
            buy_signals, sell_signals = self._detect_mean_reversion_signals(
                prices, upper_band, middle_band, lower_band, entry_threshold, exit_threshold
            )
            
            # Calculate band width and squeeze
            band_width = self._calculate_band_width(upper_band, middle_band, lower_band)
            squeeze = self._detect_squeeze(band_width)
            
            # Count generated signals
            buy_count = buy_signals.sum()
            sell_count = abs(sell_signals.sum())
            squeeze_periods = squeeze.sum()
            logger.info(f"Generated {buy_count} buy signals, {sell_count} sell signals, {squeeze_periods} squeeze periods")
            
            return {
                'upper': upper_band,
                'middle': middle_band,
                'lower': lower_band,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'squeeze': squeeze,
                'band_width': band_width
            }
            
        except Exception as e:
            logger.error(f"Error generating Bollinger Bands signals: {e}")
            return self._empty_signals(prices.index)
    
    def _detect_mean_reversion_signals(
        self,
        prices: pd.Series,
        upper_band: pd.Series,
        middle_band: pd.Series,
        lower_band: pd.Series,
        entry_threshold: float,
        exit_threshold: float
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Detect mean reversion signals based on Bollinger Bands
        
        Strategy Logic:
        - BUY when price touches or goes below lower band (oversold)
        - SELL when price touches or goes above upper band (overbought)
        - Consider band width for signal strength
        
        Args:
            prices: Price series
            upper_band, middle_band, lower_band: Bollinger Band components
            entry_threshold: Distance from band as % of price for signal
            exit_threshold: Distance from middle for exit consideration
            
        Returns:
            Tuple of (buy_signals, sell_signals) Series
        """
        try:
            # Initialize signal arrays
            buy_signals = pd.Series(0, index=prices.index, dtype=int)
            sell_signals = pd.Series(0, index=prices.index, dtype=int)
            
            # Calculate distance from bands as percentage of price
            upper_distance = (upper_band - prices) / prices
            lower_distance = (prices - lower_band) / prices
            middle_distance = abs(prices - middle_band) / middle_band
            
            # Generate oversold buy signals (price near or below lower band)
            oversold_mask = (
                (lower_distance <= entry_threshold) |  # Price at or below lower band
                (prices <= lower_band)                  # Price actually below lower band
            )
            
            # Generate overbought sell signals (price near or above upper band)
            overbought_mask = (
                (upper_distance <= entry_threshold) |  # Price at or above upper band
                (prices >= upper_band)                  # Price actually above upper band
            )
            
            # Apply signals with additional filters
            # Only signal when we have valid data
            valid_data_mask = pd.notna(upper_band) & pd.notna(lower_band) & pd.notna(middle_band)
            
            buy_signals[oversold_mask & valid_data_mask] = 1
            sell_signals[overbought_mask & valid_data_mask] = -1
            
            # Filter out signals that are too close together (reduce noise)
            buy_signals = self._filter_consecutive_signals(buy_signals, min_gap=3)
            sell_signals = self._filter_consecutive_signals(sell_signals, min_gap=3)
            
            return buy_signals, sell_signals
            
        except Exception as e:
            logger.error(f"Error detecting Bollinger Bands mean reversion signals: {e}")
            empty_series = pd.Series(0, index=prices.index, dtype=int)
            return empty_series, empty_series
    
    def _filter_consecutive_signals(self, signals: pd.Series, min_gap: int = 3) -> pd.Series:
        """
        Filter out signals that are too close together
        
        Args:
            signals: Series with signal values
            min_gap: Minimum periods between signals
            
        Returns:
            Filtered signal series
        """
        try:
            filtered = signals.copy()
            signal_indices = signals[signals != 0].index
            
            if len(signal_indices) <= 1:
                return filtered
            
            # Remove signals that are too close to previous signal
            for i in range(1, len(signal_indices)):
                current_idx = signal_indices[i]
                previous_idx = signal_indices[i-1]
                
                # Calculate gap between signals
                gap = signals.index.get_loc(current_idx) - signals.index.get_loc(previous_idx)
                
                if gap < min_gap:
                    filtered[current_idx] = 0
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering consecutive signals: {e}")
            return signals
    
    def _calculate_band_width(
        self,
        upper_band: pd.Series,
        middle_band: pd.Series,
        lower_band: pd.Series
    ) -> pd.Series:
        """
        Calculate Bollinger Band width normalized to middle band
        
        Args:
            upper_band, middle_band, lower_band: Bollinger Band components
            
        Returns:
            Series of normalized band width values
        """
        try:
            # Band width as percentage of middle band
            band_width = (upper_band - lower_band) / middle_band
            
            return band_width
            
        except Exception as e:
            logger.error(f"Error calculating band width: {e}")
            return pd.Series(0.0, index=upper_band.index)
    
    def _detect_squeeze(
        self,
        band_width: pd.Series,
        lookback: int = 20,
        percentile: float = 20
    ) -> pd.Series:
        """
        Detect Bollinger Band squeeze (low volatility periods)
        
        Args:
            band_width: Series of band width values
            lookback: Lookback period for percentile calculation
            percentile: Percentile threshold for squeeze detection
            
        Returns:
            Series with 1 for squeeze periods, 0 otherwise
        """
        try:
            # Calculate rolling percentile
            rolling_percentile = band_width.rolling(
                window=lookback, 
                min_periods=min(5, lookback)
            ).quantile(percentile / 100.0)
            
            # Squeeze when current band width is below percentile threshold
            squeeze = (band_width <= rolling_percentile).astype(int)
            
            return squeeze
            
        except Exception as e:
            logger.error(f"Error detecting squeeze: {e}")
            return pd.Series(0, index=band_width.index, dtype=int)
    
    def _empty_signals(self, index: pd.Index) -> Dict[str, pd.Series]:
        """Return empty signal structure for error cases"""
        return {
            'upper': pd.Series(dtype=float, index=index),
            'middle': pd.Series(dtype=float, index=index),
            'lower': pd.Series(dtype=float, index=index),
            'buy_signals': pd.Series(0, index=index, dtype=int),
            'sell_signals': pd.Series(0, index=index, dtype=int),
            'squeeze': pd.Series(0, index=index, dtype=int),
            'band_width': pd.Series(0.0, index=index)
        }
    
    async def validate_parameters(
        self,
        period: int,
        std_dev: float
    ) -> Dict[str, bool]:
        """
        Validate Bollinger Bands parameter configuration
        
        Args:
            period: Moving average period
            std_dev: Number of standard deviations
            
        Returns:
            Dictionary with validation results and error messages
        """
        validation = {
            'valid': True,
            'errors': []
        }
        
        # Check period constraints
        if period <= 0 or period > 100:
            validation['valid'] = False
            validation['errors'].append(f"Period must be 1-100, got {period}")
        
        if period < 10:
            validation['errors'].append(f"Warning: Period {period} may be too short for reliable signals")
        
        # Check standard deviation constraints
        if std_dev <= 0 or std_dev > 5.0:
            validation['valid'] = False
            validation['errors'].append(f"Standard deviation must be 0.1-5.0, got {std_dev}")
        
        if std_dev < 1.5 or std_dev > 2.5:
            validation['errors'].append(f"Warning: Standard deviation {std_dev} outside typical range (1.5-2.5)")
        
        logger.info(f"Bollinger Bands parameter validation: {validation}")
        return validation
    
    async def get_strategy_description(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> str:
        """
        Get human-readable strategy description
        
        Args:
            period: Moving average period
            std_dev: Number of standard deviations
            
        Returns:
            Strategy description string
        """
        return (
            f"Bollinger Bands Mean Reversion Strategy: "
            f"SMA({period}) ± {std_dev}σ bands. "
            f"Buy when price touches lower band (oversold), "
            f"sell when price touches upper band (overbought)."
        )