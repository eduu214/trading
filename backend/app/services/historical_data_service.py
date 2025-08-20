"""
Historical Data Service with Market Data Fallback System
F002-US001 Slice 3 Task 14: Enhanced with Polygon.io fallback and retry logic
Fetches historical market data for backtesting with robust error handling
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf
from loguru import logger
import asyncio
import time
from app.core.config import settings

class HistoricalDataService:
    """
    Fetches historical data for backtesting with fallback system
    F002-US001 Slice 3 Task 14: Market Data Fallback System
    
    Data Source Priority:
    1. yfinance (primary - free, reliable)
    2. Polygon.io (secondary - API key required)
    3. Mock data (fallback for testing)
    
    Features:
    - Automatic retry logic with exponential backoff
    - 5-second failover requirement compliance
    - Comprehensive error logging
    """
    
    def __init__(self):
        """Initialize the historical data service with fallback configuration"""
        self.cache = {}
        self.default_period = "6mo"  # 6 months of data as per requirements
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 5.0   # Maximum delay to meet 5-second requirement
        
        # API configuration
        self.polygon_api_key = getattr(settings, 'POLYGON_API_KEY', None)
        self.use_polygon = self.polygon_api_key is not None
        
        # Performance tracking
        self.fallback_stats = {
            'total_requests': 0,
            'yfinance_success': 0,
            'polygon_success': 0,
            'mock_fallbacks': 0,
            'avg_response_time': 0.0
        }
        
    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Get historical OHLCV data with fallback system
        F002-US001 Slice 3 Task 14: Enhanced with retry logic and failover
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (1d, 1h, 5m, etc.)
            
        Returns:
            Tuple of (DataFrame with OHLCV data, metadata dict)
        """
        start_time = time.time()
        self.fallback_stats['total_requests'] += 1
        
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
                elapsed = time.time() - start_time
                return self.cache[cache_key]['data'], {
                    **self.cache[cache_key]['metadata'],
                    'response_time': elapsed,
                    'from_cache': True
                }
            
            # Try data sources with fallback logic
            data, metadata = await self._fetch_with_fallback(symbol, start_date, end_date, interval)
            
            # Ensure we have required columns
            data = self._validate_and_clean_data(data)
            
            # Cache the data with metadata
            elapsed = time.time() - start_time
            metadata.update({
                'response_time': elapsed,
                'cached_at': datetime.utcnow(),
                'from_cache': False
            })
            
            self.cache[cache_key] = {
                'data': data,
                'metadata': metadata
            }
            
            # Update performance stats
            self._update_stats(elapsed)
            
            logger.info(f"Retrieved {len(data)} data points for {symbol} from {metadata['source']} in {elapsed:.2f}s")
            return data, metadata
            
        except Exception as e:
            logger.error(f"Critical error getting historical data for {symbol}: {e}")
            # Emergency fallback to mock data
            data = await self._generate_mock_data(symbol, start_date, end_date)
            elapsed = time.time() - start_time
            self.fallback_stats['mock_fallbacks'] += 1
            
            return data, {
                'source': 'mock_emergency',
                'response_time': elapsed,
                'error': str(e),
                'success': False
            }
    
    async def _fetch_with_fallback(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch data with automatic fallback system
        F002-US001 Slice 3 Task 14: Implements 5-second failover requirement
        
        Data source priority:
        1. yfinance (primary)
        2. Polygon.io (if API key available)
        3. Mock data (final fallback)
        """
        errors = []
        
        # Try yfinance first (most reliable for backtesting)
        try:
            data = await self._fetch_with_retry(
                self._fetch_from_yfinance,
                symbol, start_date, end_date, interval
            )
            if data is not None and not data.empty:
                self.fallback_stats['yfinance_success'] += 1
                return data, {
                    'source': 'yfinance',
                    'success': True,
                    'rows': len(data)
                }
        except Exception as e:
            error_msg = f"yfinance failed: {e}"
            errors.append(error_msg)
            logger.warning(error_msg)
        
        # Try Polygon.io if available
        if self.use_polygon:
            try:
                data = await self._fetch_with_retry(
                    self._fetch_from_polygon,
                    symbol, start_date, end_date, interval
                )
                if data is not None and not data.empty:
                    self.fallback_stats['polygon_success'] += 1
                    return data, {
                        'source': 'polygon',
                        'success': True,
                        'rows': len(data),
                        'fallback_reason': errors[0] if errors else None
                    }
            except Exception as e:
                error_msg = f"Polygon.io failed: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        # Final fallback to mock data
        logger.warning(f"All data sources failed for {symbol}, using mock data. Errors: {errors}")
        data = await self._generate_mock_data(symbol, start_date, end_date)
        self.fallback_stats['mock_fallbacks'] += 1
        
        return data, {
            'source': 'mock',
            'success': False,
            'rows': len(data),
            'errors': errors
        }
    
    async def _fetch_with_retry(
        self,
        fetch_func,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data with exponential backoff retry logic
        Ensures 5-second maximum failover time
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await fetch_func(symbol, start_date, end_date, interval)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries} for {symbol} after {delay}s delay")
                    await asyncio.sleep(delay)
        
        # All retries failed
        if last_exception:
            raise last_exception
        return None
    
    async def _fetch_from_polygon(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from Polygon.io API with rate limiting
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Import polygon only if API key is available
            from polygon import RESTClient
            
            if not self.polygon_api_key:
                raise Exception("Polygon API key not configured")
            
            # Initialize Polygon client
            client = RESTClient(self.polygon_api_key)
            
            # Convert interval format for Polygon API
            polygon_timespan = self._convert_interval_to_polygon(interval)
            
            # Fetch data
            loop = asyncio.get_event_loop()
            
            def fetch():
                aggs = client.get_aggs(
                    ticker=symbol,
                    multiplier=1,
                    timespan=polygon_timespan,
                    from_=start_date.strftime('%Y-%m-%d'),
                    to=end_date.strftime('%Y-%m-%d'),
                    adjusted=True,
                    sort='asc',
                    limit=50000
                )
                
                # Convert to DataFrame
                data_list = []
                for agg in aggs:
                    data_list.append({
                        'timestamp': agg.timestamp,
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close,
                        'volume': agg.volume
                    })
                
                if not data_list:
                    return None
                
                df = pd.DataFrame(data_list)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                return df
            
            data = await loop.run_in_executor(None, fetch)
            
            if data is not None and not data.empty:
                logger.info(f"Successfully fetched {len(data)} records from Polygon for {symbol}")
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Polygon: {e}")
            return None
    
    def _convert_interval_to_polygon(self, interval: str) -> str:
        """Convert yfinance interval format to Polygon timespan"""
        mapping = {
            '1d': 'day',
            '1h': 'hour',
            '5m': 'minute',
            '15m': 'minute',
            '30m': 'minute',
            '1m': 'minute'
        }
        return mapping.get(interval, 'day')
    
    def _update_stats(self, response_time: float):
        """Update performance statistics"""
        current_avg = self.fallback_stats['avg_response_time']
        total_requests = self.fallback_stats['total_requests']
        
        # Calculate rolling average
        self.fallback_stats['avg_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    async def get_fallback_stats(self) -> Dict:
        """Get current fallback system statistics"""
        return {
            **self.fallback_stats,
            'polygon_available': self.use_polygon,
            'yfinance_success_rate': (
                self.fallback_stats['yfinance_success'] / max(1, self.fallback_stats['total_requests'])
            ) * 100,
            'polygon_success_rate': (
                self.fallback_stats['polygon_success'] / max(1, self.fallback_stats['total_requests'])
            ) * 100 if self.use_polygon else 0,
            'mock_fallback_rate': (
                self.fallback_stats['mock_fallbacks'] / max(1, self.fallback_stats['total_requests'])
            ) * 100
        }
    
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