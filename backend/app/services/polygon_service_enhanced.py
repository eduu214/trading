import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime, timedelta
import logging
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import WebSocketMessage, Market, Feed
from app.core.config import settings
import time
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 5):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls
        
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [t for t in self.calls if now - t < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            # Need to wait
            oldest_call = self.calls[0]
            wait_time = 60 - (now - oldest_call) + 0.1  # Add small buffer
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Record this call
        self.calls.append(now)


def rate_limited(func):
    """Decorator to apply rate limiting to async functions"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if hasattr(self, 'rate_limiter'):
            self.rate_limiter.wait_if_needed()
        return await func(self, *args, **kwargs)
    return wrapper


class PolygonServiceEnhanced:
    """Enhanced Polygon service with rate limiting and free tier handling"""
    
    def __init__(self):
        self.api_key = settings.POLYGON_API_KEY
        # Use official Polygon client
        self.rest_client = RESTClient(api_key=self.api_key) if self.api_key else None
        self.ws_client: Optional[WebSocketClient] = None
        # Rate limiter for free tier (5 calls per minute)
        self.rate_limiter = RateLimiter(calls_per_minute=5)
        self.is_free_tier = True  # Assume free tier by default
        
    def _use_historical_date(self) -> datetime:
        """Get a date that works with free tier (2+ days ago)"""
        # Free tier can't access data from today or yesterday
        return datetime.now() - timedelta(days=3)
    
    @rate_limited
    async def get_tickers(self, market: str = "stocks", active: bool = True, limit: int = 100) -> List[Dict]:
        """
        Get list of tickers for a given market with rate limiting
        Reduced limit for free tier
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized - API key missing")
            return self._get_mock_tickers()
            
        try:
            tickers = []
            # Reduce limit for free tier
            actual_limit = min(limit, 100) if self.is_free_tier else limit
            
            # Use the official client's list_tickers method
            for ticker in self.rest_client.list_tickers(
                market=market,
                active=active,
                limit=actual_limit
            ):
                tickers.append({
                    "ticker": ticker.ticker,
                    "name": ticker.name,
                    "market": ticker.market,
                    "locale": ticker.locale,
                    "type": ticker.type,
                    "currency_name": ticker.currency_name,
                    "active": ticker.active
                })
            return tickers
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning("Rate limit hit - using mock data")
                return self._get_mock_tickers()
            elif "upgrade" in str(e).lower():
                logger.warning("Free tier limitation - using mock data")
                self.is_free_tier = True
                return self._get_mock_tickers()
            logger.error(f"Error fetching tickers: {e}")
            return self._get_mock_tickers()
            
    @rate_limited
    async def get_aggregates(
        self, 
        ticker: str, 
        multiplier: int = 1,
        timespan: str = "day",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get aggregate bars for a ticker with rate limiting and free tier handling
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized - API key missing")
            return self._get_mock_aggregates(ticker)
            
        # Adjust dates for free tier - can't get today's data
        if self.is_free_tier:
            historical_date = self._use_historical_date()
            if not to_date or to_date > historical_date:
                to_date = historical_date
            if not from_date:
                from_date = to_date - timedelta(days=30)
        else:
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")
        
        try:
            aggs = []
            # Use the official client's list_aggs method
            for agg in self.rest_client.list_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_str,
                to=to_str,
                limit=500 if self.is_free_tier else 50000
            ):
                aggs.append({
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap if hasattr(agg, 'vwap') else None,
                    "timestamp": agg.timestamp,
                    "transactions": agg.transactions if hasattr(agg, 'transactions') else None
                })
            return aggs
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning(f"Rate limit hit for {ticker} - using mock data")
                return self._get_mock_aggregates(ticker)
            elif "upgrade" in str(e).lower() or "before end of day" in str(e).lower():
                logger.warning(f"Free tier limitation for {ticker} - adjusting date range")
                self.is_free_tier = True
                # Retry with historical dates
                return await self.get_aggregates(ticker, multiplier, timespan, from_date, self._use_historical_date())
            logger.error(f"Error fetching aggregates for {ticker}: {e}")
            return self._get_mock_aggregates(ticker)
    
    @rate_limited
    async def get_last_trade(self, ticker: str) -> Optional[Dict]:
        """
        Get the last trade for a ticker with rate limiting
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return self._get_mock_last_trade(ticker)
            
        try:
            trade = self.rest_client.get_last_trade(ticker=ticker)
            if trade:
                return {
                    "ticker": ticker,
                    "price": trade.price,
                    "size": trade.size,
                    "timestamp": trade.timestamp,
                    "conditions": trade.conditions if hasattr(trade, 'conditions') else [],
                    "exchange": trade.exchange if hasattr(trade, 'exchange') else None
                }
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning(f"Rate limit hit - using mock data for {ticker}")
                return self._get_mock_last_trade(ticker)
            logger.error(f"Error fetching last trade for {ticker}: {e}")
            return self._get_mock_last_trade(ticker)
    
    @rate_limited
    async def get_last_quote(self, ticker: str) -> Optional[Dict]:
        """
        Get the last quote for a ticker with rate limiting
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return self._get_mock_last_quote(ticker)
            
        try:
            quote = self.rest_client.get_last_quote(ticker=ticker)
            if quote:
                return {
                    "ticker": ticker,
                    "bid": quote.bid_price if hasattr(quote, 'bid_price') else 0,
                    "bid_size": quote.bid_size if hasattr(quote, 'bid_size') else 0,
                    "ask": quote.ask_price if hasattr(quote, 'ask_price') else 0,
                    "ask_size": quote.ask_size if hasattr(quote, 'ask_size') else 0,
                    "timestamp": quote.timestamp if hasattr(quote, 'timestamp') else datetime.now().timestamp(),
                    "exchange": quote.exchange if hasattr(quote, 'exchange') else None
                }
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning(f"Rate limit hit - using mock data for {ticker}")
                return self._get_mock_last_quote(ticker)
            logger.error(f"Error fetching last quote for {ticker}: {e}")
            return self._get_mock_last_quote(ticker)
    
    async def scan_for_opportunities_limited(
        self,
        asset_classes: List[str],
        min_volume: int = 1000000,
        min_price_change: float = 0.02
    ) -> List[Dict]:
        """
        Limited scan for free tier - uses mock data or cached results
        """
        logger.info("Running limited scan for free tier")
        
        # Use a small set of popular tickers for demonstration
        demo_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
        opportunities = []
        
        for ticker in demo_tickers:
            # Get historical data (3 days ago for free tier)
            historical_date = self._use_historical_date()
            aggs = await self.get_aggregates(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_date=historical_date - timedelta(days=7),
                to_date=historical_date
            )
            
            if len(aggs) >= 2:
                recent = aggs[-1]
                previous = aggs[-2]
                
                if previous["close"] and previous["close"] > 0:
                    pct_change = (recent["close"] - previous["close"]) / previous["close"]
                    
                    if abs(pct_change) >= min_price_change:
                        opportunities.append({
                            "ticker": ticker,
                            "volume": recent["volume"],
                            "price_change": pct_change,
                            "open": recent["open"],
                            "close": recent["close"],
                            "high": recent["high"],
                            "low": recent["low"],
                            "opportunity_type": "momentum" if pct_change > 0 else "reversal",
                            "data_date": historical_date.strftime("%Y-%m-%d"),
                            "note": "Historical data - free tier limitation"
                        })
        
        # Sort by absolute price change
        opportunities.sort(key=lambda x: abs(x["price_change"]), reverse=True)
        return opportunities
    
    # Mock data methods for fallback
    def _get_mock_tickers(self) -> List[Dict]:
        """Return mock ticker data for testing"""
        return [
            {"ticker": "AAPL", "name": "Apple Inc.", "market": "stocks", "locale": "us", "type": "CS", "currency_name": "usd", "active": True},
            {"ticker": "MSFT", "name": "Microsoft Corporation", "market": "stocks", "locale": "us", "type": "CS", "currency_name": "usd", "active": True},
            {"ticker": "GOOGL", "name": "Alphabet Inc.", "market": "stocks", "locale": "us", "type": "CS", "currency_name": "usd", "active": True},
            {"ticker": "AMZN", "name": "Amazon.com Inc.", "market": "stocks", "locale": "us", "type": "CS", "currency_name": "usd", "active": True},
            {"ticker": "NVDA", "name": "NVIDIA Corporation", "market": "stocks", "locale": "us", "type": "CS", "currency_name": "usd", "active": True},
        ]
    
    def _get_mock_aggregates(self, ticker: str) -> List[Dict]:
        """Return mock aggregate data for testing"""
        import random
        base_price = {"AAPL": 180, "MSFT": 420, "GOOGL": 150, "AMZN": 170, "NVDA": 880}.get(ticker, 100)
        
        data = []
        for i in range(10):
            price = base_price * (1 + random.uniform(-0.02, 0.02))
            data.append({
                "open": price * 0.99,
                "high": price * 1.01,
                "low": price * 0.98,
                "close": price,
                "volume": random.randint(1000000, 10000000),
                "vwap": price,
                "timestamp": int((datetime.now() - timedelta(days=10-i)).timestamp() * 1000),
                "transactions": random.randint(10000, 100000)
            })
        return data
    
    def _get_mock_last_trade(self, ticker: str) -> Dict:
        """Return mock last trade data"""
        import random
        base_price = {"AAPL": 180, "MSFT": 420, "GOOGL": 150, "AMZN": 170, "NVDA": 880}.get(ticker, 100)
        return {
            "ticker": ticker,
            "price": base_price * (1 + random.uniform(-0.01, 0.01)),
            "size": random.randint(100, 1000),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "conditions": [],
            "exchange": "XNAS"
        }
    
    def _get_mock_last_quote(self, ticker: str) -> Dict:
        """Return mock last quote data"""
        import random
        base_price = {"AAPL": 180, "MSFT": 420, "GOOGL": 150, "AMZN": 170, "NVDA": 880}.get(ticker, 100)
        bid = base_price * (1 + random.uniform(-0.01, 0.01))
        return {
            "ticker": ticker,
            "bid": bid,
            "bid_size": random.randint(100, 1000),
            "ask": bid * 1.001,
            "ask_size": random.randint(100, 1000),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "exchange": "XNAS"
        }


# Singleton instance
polygon_service_enhanced = PolygonServiceEnhanced()