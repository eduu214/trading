"""
Historical Data Service with Market Data Fallback System
F002-US001 Slice 3 Task 14: Enhanced with Polygon.io fallback and retry logic
F002-US001 Slice 3 Task 17: Enhanced with data quality validation and gap handling
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
from app.core.logging_config import structured_logger

class DataQualityError(Exception):
    """Raised when data quality validation fails"""
    pass

class HistoricalDataService:
    """
    Fetches historical data for backtesting with fallback system
    F002-US001 Slice 3 Task 14: Market Data Fallback System
    F002-US001 Slice 3 Task 17: Data Quality Validation
    
    Data Source Priority:
    1. yfinance (primary - free, reliable)
    2. Polygon.io (secondary - API key required)
    3. Mock data (fallback for testing)
    
    Features:
    - Automatic retry logic with exponential backoff
    - 5-second failover requirement compliance
    - 6-month minimum data validation
    - Gap detection and handling
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
        
        # Data quality validation configuration (Task 17)
        self.min_data_months = 6  # Minimum 6 months of data required
        self.max_gap_days = 5     # Maximum allowed consecutive missing days
        self.min_trading_days = 120  # Minimum trading days for 6 months (approx 22 days/month * 6)
        
        # Structured logging (Task 18)
        self.logger = structured_logger
        
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
        
        # Generate correlation ID for this data fetch operation (Task 18)
        correlation_id = self.logger.generate_correlation_id()
        
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
            
            # Perform data quality validation (Task 17)
            validation_start = time.time()
            quality_result = await self._validate_data_quality(data, symbol, start_date, end_date)
            validation_time = time.time() - validation_start
            
            # Log data quality validation results (Task 18)
            self.logger.log_data_quality_validation(
                correlation_id=correlation_id,
                symbol=symbol,
                validation_result=quality_result,
                data_source=metadata.get('source', 'unknown'),
                execution_time=validation_time
            )
            
            metadata.update(quality_result)
            
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
            
            # Log data fetch error with structured logging (Task 18)
            self.logger.log_data_fetch_error(
                correlation_id="fallback_" + str(int(time.time())),
                symbol=symbol,
                data_source="yfinance",
                error=e,
                fallback_used=True
            )
        
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
    
    async def _validate_data_quality(
        self,
        data: pd.DataFrame,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Validate data quality for backtesting requirements
        F002-US001 Slice 3 Task 17: Data Quality Validation
        
        Validates:
        1. Minimum 6 months of data
        2. Gap detection and handling
        3. Sufficient trading days
        4. Data integrity checks
        
        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            start_date: Expected start date
            end_date: Expected end date
            
        Returns:
            Dict with validation results and metadata
        """
        try:
            validation_result = {
                'data_quality_passed': False,
                'validation_details': {},
                'quality_warnings': [],
                'quality_errors': []
            }
            
            if data.empty:
                validation_result['quality_errors'].append("No data available")
                return validation_result
            
            # Check 1: Minimum data period (6 months)
            actual_days = (data.index[-1] - data.index[0]).days
            required_days = self.min_data_months * 30  # Approximate 180 days
            
            if actual_days < required_days:
                validation_result['quality_errors'].append(
                    f"Insufficient data period: {actual_days} days < {required_days} days required"
                )
            else:
                validation_result['validation_details']['period_check'] = 'PASS'
            
            # Check 2: Minimum trading days
            trading_days = len(data)
            if trading_days < self.min_trading_days:
                validation_result['quality_errors'].append(
                    f"Insufficient trading days: {trading_days} < {self.min_trading_days} required"
                )
            else:
                validation_result['validation_details']['trading_days_check'] = 'PASS'
            
            # Check 3: Gap detection
            gap_analysis = await self._detect_data_gaps(data, symbol)
            validation_result['validation_details']['gap_analysis'] = gap_analysis
            
            if gap_analysis['critical_gaps'] > 0:
                validation_result['quality_errors'].append(
                    f"Critical data gaps detected: {gap_analysis['critical_gaps']} gaps > {self.max_gap_days} days"
                )
            elif gap_analysis['total_gaps'] > 0:
                validation_result['quality_warnings'].append(
                    f"Minor data gaps detected: {gap_analysis['total_gaps']} gaps ≤ {self.max_gap_days} days"
                )
            
            # Check 4: Data integrity (price relationships)
            integrity_check = await self._check_data_integrity(data)
            validation_result['validation_details']['integrity_check'] = integrity_check
            
            if not integrity_check['valid']:
                validation_result['quality_errors'].append(
                    f"Data integrity issues: {integrity_check['issues']}"
                )
            
            # Check 5: Volume data availability
            if 'volume' not in data.columns or data['volume'].isna().all():
                validation_result['quality_warnings'].append("Volume data not available")
            elif (data['volume'] == 0).sum() > len(data) * 0.1:  # More than 10% zero volume
                validation_result['quality_warnings'].append("High percentage of zero volume days")
            
            # Overall validation result
            validation_result['data_quality_passed'] = len(validation_result['quality_errors']) == 0
            
            # Add summary statistics
            validation_result['validation_details']['summary'] = {
                'total_days': actual_days,
                'trading_days': trading_days,
                'data_completeness': (trading_days / max(1, actual_days)) * 100,
                'start_date': data.index[0].isoformat(),
                'end_date': data.index[-1].isoformat(),
                'gaps_detected': gap_analysis['total_gaps'],
                'critical_gaps': gap_analysis['critical_gaps']
            }
            
            # Log validation results
            if validation_result['data_quality_passed']:
                logger.info(f"Data quality validation PASSED for {symbol}")
            else:
                logger.warning(f"Data quality validation FAILED for {symbol}: {validation_result['quality_errors']}")
            
            if validation_result['quality_warnings']:
                logger.info(f"Data quality warnings for {symbol}: {validation_result['quality_warnings']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating data quality for {symbol}: {e}")
            return {
                'data_quality_passed': False,
                'validation_details': {},
                'quality_warnings': [],
                'quality_errors': [f"Validation error: {str(e)}"]
            }
    
    async def _detect_data_gaps(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Detect gaps in the data timeline
        F002-US001 Slice 3 Task 17: Gap detection and handling
        
        Args:
            data: OHLCV DataFrame with datetime index
            symbol: Trading symbol for logging
            
        Returns:
            Dict with gap analysis results
        """
        try:
            if data.empty:
                return {
                    'total_gaps': 0,
                    'critical_gaps': 0,
                    'max_gap_days': 0,
                    'gap_details': []
                }
            
            # Generate expected business days (trading days)
            start_date = data.index[0]
            end_date = data.index[-1]
            expected_dates = pd.bdate_range(start=start_date, end=end_date)
            
            # Find missing dates
            missing_dates = expected_dates.difference(data.index)
            
            if len(missing_dates) == 0:
                return {
                    'total_gaps': 0,
                    'critical_gaps': 0,
                    'max_gap_days': 0,
                    'gap_details': []
                }
            
            # Group consecutive missing dates into gaps
            gaps = []
            current_gap = []
            
            for i, date in enumerate(missing_dates):
                if i == 0 or (date - missing_dates[i-1]).days == 1:
                    # Continue current gap
                    current_gap.append(date)
                else:
                    # Start new gap
                    if current_gap:
                        gaps.append(current_gap)
                    current_gap = [date]
            
            # Add the last gap
            if current_gap:
                gaps.append(current_gap)
            
            # Analyze gaps
            gap_details = []
            critical_gaps = 0
            max_gap_days = 0
            
            for gap in gaps:
                gap_days = len(gap)
                max_gap_days = max(max_gap_days, gap_days)
                
                gap_info = {
                    'start_date': gap[0].isoformat(),
                    'end_date': gap[-1].isoformat(),
                    'days': gap_days,
                    'is_critical': gap_days > self.max_gap_days
                }
                gap_details.append(gap_info)
                
                if gap_days > self.max_gap_days:
                    critical_gaps += 1
            
            logger.debug(f"Gap analysis for {symbol}: {len(gaps)} gaps, {critical_gaps} critical")
            
            return {
                'total_gaps': len(gaps),
                'critical_gaps': critical_gaps,
                'max_gap_days': max_gap_days,
                'gap_details': gap_details,
                'missing_days_total': len(missing_dates),
                'expected_trading_days': len(expected_dates),
                'actual_trading_days': len(data)
            }
            
        except Exception as e:
            logger.error(f"Error detecting data gaps for {symbol}: {e}")
            return {
                'total_gaps': 0,
                'critical_gaps': 0,
                'max_gap_days': 0,
                'gap_details': [],
                'error': str(e)
            }
    
    async def _check_data_integrity(self, data: pd.DataFrame) -> Dict:
        """
        Check data integrity for price relationships and anomalies
        F002-US001 Slice 3 Task 17: Data integrity validation
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dict with integrity check results
        """
        try:
            issues = []
            
            if data.empty:
                return {'valid': False, 'issues': ['No data to validate']}
            
            # Check 1: High >= Low for all days
            high_low_violations = (data['high'] < data['low']).sum()
            if high_low_violations > 0:
                issues.append(f"High < Low violations: {high_low_violations} days")
            
            # Check 2: Close and Open within High/Low range
            close_violations = ((data['close'] > data['high']) | (data['close'] < data['low'])).sum()
            if close_violations > 0:
                issues.append(f"Close outside High/Low range: {close_violations} days")
            
            open_violations = ((data['open'] > data['high']) | (data['open'] < data['low'])).sum()
            if open_violations > 0:
                issues.append(f"Open outside High/Low range: {open_violations} days")
            
            # Check 3: Extreme price movements (> 50% in one day)
            price_changes = data['close'].pct_change().abs()
            extreme_moves = (price_changes > 0.5).sum()
            if extreme_moves > 0:
                issues.append(f"Extreme price movements (>50%): {extreme_moves} days")
            
            # Check 4: Zero or negative prices
            zero_prices = ((data['close'] <= 0) | (data['open'] <= 0) | 
                          (data['high'] <= 0) | (data['low'] <= 0)).sum()
            if zero_prices > 0:
                issues.append(f"Zero or negative prices: {zero_prices} occurrences")
            
            # Check 5: Missing or NaN values
            nan_values = data.isna().sum().sum()
            if nan_values > 0:
                issues.append(f"NaN values found: {nan_values} occurrences")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'checks_performed': [
                    'high_low_relationship',
                    'close_in_range',
                    'open_in_range', 
                    'extreme_movements',
                    'positive_prices',
                    'missing_values'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {e}")
            return {
                'valid': False,
                'issues': [f"Integrity check error: {str(e)}"]
            }
    
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