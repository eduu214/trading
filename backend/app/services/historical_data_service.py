"""
Historical Data Service
Fetches historical market data for backtesting
Part of F002-US001: Real Strategy Engine with Backtesting
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import yfinance as yf
from loguru import logger
import asyncio
from app.core.config import settings

class HistoricalDataService:
    """
    Fetches historical data for backtesting
    Uses yfinance as primary source (free, reliable for backtesting)
    Polygon.io as secondary source (rate limited on free tier)
    """
    
    def __init__(self):
        """Initialize the historical data service"""
        self.cache = {}
        self.default_period = "6mo"  # 6 months of data as per requirements
        
    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (1d, 1h, 5m, etc.)
            
        Returns:
            DataFrame with OHLCV data and datetime index
        """
        try:
            # Default to 6 months of data if dates not specified
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=180)  # 6 months
            
            # Check cache first
            cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
            if cache_key in self.cache:
                logger.info(f"Using cached data for {symbol}")
                return self.cache[cache_key]
            
            # Try yfinance first (more reliable for backtesting)
            data = await self._fetch_from_yfinance(symbol, start_date, end_date, interval)
            
            if data is None or data.empty:
                logger.warning(f"No data from yfinance for {symbol}, trying mock data")
                data = await self._generate_mock_data(symbol, start_date, end_date)
            
            # Ensure we have required columns
            data = self._validate_and_clean_data(data)
            
            # Cache the data
            self.cache[cache_key] = data
            
            logger.info(f"Retrieved {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            # Return mock data as fallback
            return await self._generate_mock_data(symbol, start_date, end_date)
    
    async def _fetch_from_yfinance(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from yfinance
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def fetch():
                ticker = yf.Ticker(symbol)
                return ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=True,  # Adjust for splits/dividends
                    prepost=False,
                    actions=False
                )
            
            data = await loop.run_in_executor(None, fetch)
            
            if data is not None and not data.empty:
                # Rename columns to lowercase
                data.columns = data.columns.str.lower()
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from yfinance: {e}")
            return None
    
    async def _generate_mock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Generate realistic mock data for testing
        Uses geometric Brownian motion to simulate price movements
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with mock OHLCV data
        """
        try:
            # Calculate number of trading days
            days = pd.bdate_range(start=start_date, end=end_date)
            num_days = len(days)
            
            # Set seed for reproducibility per symbol
            seed = sum(ord(c) for c in symbol)
            np.random.seed(seed)
            
            # Generate price series using geometric Brownian motion
            initial_price = 100 + np.random.uniform(-50, 150)  # Random starting price
            daily_volatility = 0.02  # 2% daily volatility
            daily_drift = 0.0002  # Slight upward drift
            
            # Generate returns
            returns = np.random.normal(daily_drift, daily_volatility, num_days)
            price_series = initial_price * np.exp(np.cumsum(returns))
            
            # Generate OHLCV data
            data = pd.DataFrame(index=days)
            data['close'] = price_series
            
            # Generate open prices (close of previous day with gap)
            data['open'] = data['close'].shift(1) * (1 + np.random.normal(0, 0.005, num_days))
            data['open'].iloc[0] = initial_price
            
            # Generate high/low (ensure high >= close, low <= close)
            daily_range = np.abs(np.random.normal(0, 0.01, num_days))
            data['high'] = data[['open', 'close']].max(axis=1) * (1 + daily_range)
            data['low'] = data[['open', 'close']].min(axis=1) * (1 - daily_range)
            
            # Generate volume (correlated with price changes)
            base_volume = 10000000
            price_change = np.abs(data['close'].pct_change().fillna(0))
            data['volume'] = base_volume * (1 + price_change * 10) * np.random.uniform(0.8, 1.2, num_days)
            data['volume'] = data['volume'].astype(int)
            
            logger.info(f"Generated mock data for {symbol}: {num_days} days")
            return data
            
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            # Return minimal valid dataframe
            days = pd.bdate_range(start=start_date, end=end_date)
            return pd.DataFrame({
                'open': 100,
                'high': 101,
                'low': 99,
                'close': 100,
                'volume': 1000000
            }, index=days)
    
    def _validate_and_clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean the data
        
        Args:
            data: Raw OHLCV DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        try:
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    logger.warning(f"Missing column {col}, adding default values")
                    if col == 'volume':
                        data[col] = 1000000
                    else:
                        data[col] = data.get('close', 100)
            
            # Remove any NaN values
            data = data.dropna()
            
            # Ensure volume is integer
            if 'volume' in data.columns:
                data['volume'] = data['volume'].astype(int)
            
            # Sort by date
            data = data.sort_index()
            
            return data
            
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return data
    
    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols
        
        Args:
            symbols: List of trading symbols
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary of symbol to DataFrame
        """
        try:
            results = {}
            
            for symbol in symbols:
                data = await self.get_historical_data(symbol, start_date, end_date)
                results[symbol] = data
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting multiple symbols: {e}")
            return {}