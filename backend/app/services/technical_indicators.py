"""
Technical Indicator Service
Calculates standardized technical indicators for trading strategies
Part of F002-US001: Real Strategy Engine with Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from loguru import logger
import talib
from datetime import datetime, timedelta
import redis
import json
from app.core.config import settings

class TechnicalIndicatorService:
    """Calculate and cache technical indicators using TA-Lib"""
    
    def __init__(self):
        """Initialize the technical indicator service with Redis caching"""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.cache_ttl = 3600  # 1 hour cache
        
    def _get_cache_key(self, symbol: str, indicator: str, timeframe: str, period: int = None) -> str:
        """Generate a cache key for indicator results"""
        if period:
            return f"indicator:{symbol}:{indicator}:{timeframe}:{period}"
        return f"indicator:{symbol}:{indicator}:{timeframe}"
    
    async def calculate_rsi(
        self, 
        prices: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            Series of RSI values
        """
        try:
            if len(prices) < period + 1:
                logger.warning(f"Insufficient data for RSI calculation. Need {period + 1}, got {len(prices)}")
                return pd.Series(dtype=float)
            
            # Calculate RSI using TA-Lib
            rsi = talib.RSI(prices.values, timeperiod=period)
            
            return pd.Series(rsi, index=prices.index)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            raise
    
    async def calculate_macd(
        self, 
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Series of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            
        Returns:
            Dictionary with 'macd', 'signal', and 'histogram' Series
        """
        try:
            min_required = slow_period + signal_period
            if len(prices) < min_required:
                logger.warning(f"Insufficient data for MACD. Need {min_required}, got {len(prices)}")
                return {
                    'macd': pd.Series(dtype=float),
                    'signal': pd.Series(dtype=float),
                    'histogram': pd.Series(dtype=float)
                }
            
            # Calculate MACD using TA-Lib
            macd, signal, histogram = talib.MACD(
                prices.values,
                fastperiod=fast_period,
                slowperiod=slow_period,
                signalperiod=signal_period
            )
            
            return {
                'macd': pd.Series(macd, index=prices.index),
                'signal': pd.Series(signal, index=prices.index),
                'histogram': pd.Series(histogram, index=prices.index)
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            raise
    
    async def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: Series of closing prices
            period: Moving average period (default 20)
            std_dev: Number of standard deviations (default 2.0)
            
        Returns:
            Dictionary with 'upper', 'middle', and 'lower' band Series
        """
        try:
            if len(prices) < period:
                logger.warning(f"Insufficient data for Bollinger Bands. Need {period}, got {len(prices)}")
                return {
                    'upper': pd.Series(dtype=float),
                    'middle': pd.Series(dtype=float),
                    'lower': pd.Series(dtype=float)
                }
            
            # Calculate Bollinger Bands using TA-Lib
            upper, middle, lower = talib.BBANDS(
                prices.values,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev,
                matype=0  # Simple Moving Average
            )
            
            return {
                'upper': pd.Series(upper, index=prices.index),
                'middle': pd.Series(middle, index=prices.index),
                'lower': pd.Series(lower, index=prices.index)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            raise
    
    async def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            period: ATR period (default 14)
            
        Returns:
            Series of ATR values
        """
        try:
            if len(high) < period + 1:
                logger.warning(f"Insufficient data for ATR. Need {period + 1}, got {len(high)}")
                return pd.Series(dtype=float)
            
            # Calculate ATR using TA-Lib
            atr = talib.ATR(high.values, low.values, close.values, timeperiod=period)
            
            return pd.Series(atr, index=close.index)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            raise
    
    async def get_cached_indicator(
        self,
        symbol: str,
        indicator: str,
        timeframe: str,
        period: int = None
    ) -> Optional[pd.Series]:
        """
        Retrieve cached indicator values
        
        Args:
            symbol: Trading symbol
            indicator: Indicator name (RSI, MACD, etc.)
            timeframe: Timeframe (1D, 1H, etc.)
            period: Indicator period (if applicable)
            
        Returns:
            Cached Series or None if not found
        """
        try:
            cache_key = self._get_cache_key(symbol, indicator, timeframe, period)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return pd.Series(data['values'], index=pd.to_datetime(data['index']))
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached indicator: {e}")
            return None
    
    async def cache_indicator(
        self,
        symbol: str,
        indicator: str,
        timeframe: str,
        data: pd.Series,
        period: int = None
    ) -> None:
        """
        Cache indicator values
        
        Args:
            symbol: Trading symbol
            indicator: Indicator name
            timeframe: Timeframe
            data: Indicator values to cache
            period: Indicator period (if applicable)
        """
        try:
            cache_key = self._get_cache_key(symbol, indicator, timeframe, period)
            cache_data = {
                'values': data.tolist(),
                'index': data.index.astype(str).tolist(),
                'cached_at': datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.error(f"Error caching indicator: {e}")
    
    async def calculate_all_indicators(
        self,
        symbol: str,
        prices_df: pd.DataFrame,
        timeframe: str = "1D"
    ) -> Dict[str, pd.Series]:
        """
        Calculate all standard indicators for a symbol
        
        Args:
            symbol: Trading symbol
            prices_df: DataFrame with OHLCV data
            timeframe: Timeframe for caching
            
        Returns:
            Dictionary of all calculated indicators
        """
        try:
            results = {}
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in prices_df.columns:
                    logger.error(f"Missing required column: {col}")
                    return results
            
            # Calculate RSI
            rsi = await self.calculate_rsi(prices_df['close'])
            results['rsi'] = rsi
            await self.cache_indicator(symbol, 'rsi', timeframe, rsi, 14)
            
            # Calculate MACD
            macd_data = await self.calculate_macd(prices_df['close'])
            results.update(macd_data)
            
            # Calculate Bollinger Bands
            bb_data = await self.calculate_bollinger_bands(prices_df['close'])
            results['bb_upper'] = bb_data['upper']
            results['bb_middle'] = bb_data['middle']
            results['bb_lower'] = bb_data['lower']
            
            # Calculate ATR for volatility
            atr = await self.calculate_atr(
                prices_df['high'],
                prices_df['low'],
                prices_df['close']
            )
            results['atr'] = atr
            
            logger.info(f"Calculated all indicators for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Error calculating all indicators for {symbol}: {e}")
            return {}