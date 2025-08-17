import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime, timedelta
import logging
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import WebSocketMessage, Market, Feed
from app.core.config import settings

logger = logging.getLogger(__name__)


class PolygonService:
    """Service for interacting with Polygon.io API using official client"""
    
    def __init__(self):
        self.api_key = settings.POLYGON_API_KEY
        # Use official Polygon client
        self.rest_client = RESTClient(api_key=self.api_key) if self.api_key else None
        self.ws_client: Optional[WebSocketClient] = None
        
    async def get_tickers(self, market: str = "stocks", active: bool = True, limit: int = 1000) -> List[Dict]:
        """
        Get list of tickers for a given market using official client
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return []
            
        try:
            tickers = []
            # Use the official client's list_tickers method
            for ticker in self.rest_client.list_tickers(
                market=market,
                active=active,
                limit=limit
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
            logger.error(f"Error fetching tickers: {e}")
            return []
            
    async def get_aggregates(
        self, 
        ticker: str, 
        multiplier: int = 1,
        timespan: str = "day",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get aggregate bars for a ticker using official client
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return []
            
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
                limit=50000
            ):
                aggs.append({
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap,
                    "timestamp": agg.timestamp,
                    "transactions": agg.transactions
                })
            return aggs
        except Exception as e:
            logger.error(f"Error fetching aggregates: {e}")
            return []
            
    async def get_snapshot_all_tickers(self) -> Dict:
        """
        Get snapshot of all tickers using official client
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return {}
            
        try:
            snapshots = {}
            # Use the official client's list_universal_snapshots method
            for snapshot in self.rest_client.list_universal_snapshots():
                snapshots[snapshot.ticker] = {
                    "ticker": snapshot.ticker,
                    "type": snapshot.type,
                    "session": {
                        "open": snapshot.session.open if snapshot.session else None,
                        "high": snapshot.session.high if snapshot.session else None,
                        "low": snapshot.session.low if snapshot.session else None,
                        "close": snapshot.session.close if snapshot.session else None,
                        "volume": snapshot.session.volume if snapshot.session else None
                    } if snapshot.session else None,
                    "price": snapshot.price,
                    "updated": snapshot.updated
                }
            return snapshots
        except Exception as e:
            logger.error(f"Error fetching snapshots: {e}")
            return {}
            
    async def get_last_trade(self, ticker: str) -> Optional[Dict]:
        """
        Get the last trade for a ticker using official client
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return None
            
        try:
            trade = self.rest_client.get_last_trade(ticker=ticker)
            if trade:
                return {
                    "ticker": ticker,
                    "price": trade.price,
                    "size": trade.size,
                    "timestamp": trade.timestamp,
                    "conditions": trade.conditions,
                    "exchange": trade.exchange
                }
        except Exception as e:
            logger.error(f"Error fetching last trade: {e}")
            return None
            
    async def get_last_quote(self, ticker: str) -> Optional[Dict]:
        """
        Get the last quote for a ticker using official client
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return None
            
        try:
            quote = self.rest_client.get_last_quote(ticker=ticker)
            if quote:
                return {
                    "ticker": ticker,
                    "bid": quote.bid_price,
                    "bid_size": quote.bid_size,
                    "ask": quote.ask_price,
                    "ask_size": quote.ask_size,
                    "timestamp": quote.timestamp,
                    "exchange": quote.exchange
                }
        except Exception as e:
            logger.error(f"Error fetching last quote: {e}")
            return None
            
    async def get_grouped_daily(self, date: str) -> List[Dict]:
        """
        Get grouped daily aggregates for all tickers on a specific date
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return []
            
        try:
            results = []
            response = self.rest_client.get_grouped_daily_aggs(date=date)
            
            if response and hasattr(response, 'results'):
                for agg in response.results:
                    results.append({
                        "ticker": agg.ticker,
                        "open": agg.open,
                        "high": agg.high,
                        "low": agg.low,
                        "close": agg.close,
                        "volume": agg.volume,
                        "vwap": agg.vwap,
                        "timestamp": agg.timestamp
                    })
            return results
        except Exception as e:
            logger.error(f"Error fetching grouped daily: {e}")
            return []
            
    def setup_websocket(self, symbols: List[str], on_message=None):
        """
        Setup WebSocket connection for real-time data using official client
        """
        if not self.api_key:
            logger.error("Polygon API key not configured")
            return None
            
        try:
            # Create subscriptions for trades and quotes
            subscriptions = []
            for symbol in symbols:
                subscriptions.append(f"T.{symbol}")  # Trades
                subscriptions.append(f"Q.{symbol}")  # Quotes
                subscriptions.append(f"A.{symbol}")  # Aggregates (per second)
                
            # Initialize WebSocket client with subscriptions
            self.ws_client = WebSocketClient(
                api_key=self.api_key,
                subscriptions=subscriptions,
                market=Market.Stocks  # Can be changed for other markets
            )
            
            # Set up message handler
            def handle_msg(msgs: List[WebSocketMessage]):
                for msg in msgs:
                    if on_message:
                        on_message(msg)
                    else:
                        logger.info(f"WebSocket message: {msg}")
                        
            # Run the WebSocket client
            self.ws_client.run(handle_msg=handle_msg)
            
        except Exception as e:
            logger.error(f"WebSocket setup error: {e}")
            
    async def get_market_status(self) -> Dict:
        """
        Get current market status
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return {}
            
        try:
            status = self.rest_client.get_market_status()
            return {
                "market": status.market,
                "server_time": status.server_time,
                "exchanges": {
                    ex.exchange: ex.status 
                    for ex in status.exchanges
                } if hasattr(status, 'exchanges') else {},
                "currencies": {
                    curr.currency: curr.status 
                    for curr in status.currencies
                } if hasattr(status, 'currencies') else {}
            }
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            return {}
            
    async def scan_for_opportunities(
        self,
        asset_classes: List[str],
        min_volume: int = 1000000,
        min_price_change: float = 0.02
    ) -> List[Dict]:
        """
        Scan markets for trading opportunities
        """
        if not self.rest_client:
            logger.error("Polygon REST client not initialized")
            return []
            
        opportunities = []
        
        try:
            # Get today's grouped daily data
            today = datetime.now().strftime("%Y-%m-%d")
            daily_data = await self.get_grouped_daily(today)
            
            for ticker_data in daily_data:
                # Calculate percentage change
                if ticker_data["open"] > 0:
                    pct_change = (ticker_data["close"] - ticker_data["open"]) / ticker_data["open"]
                    
                    # Check for opportunities based on criteria
                    if (ticker_data["volume"] >= min_volume and 
                        abs(pct_change) >= min_price_change):
                        
                        opportunities.append({
                            "ticker": ticker_data["ticker"],
                            "volume": ticker_data["volume"],
                            "price_change": pct_change,
                            "open": ticker_data["open"],
                            "close": ticker_data["close"],
                            "high": ticker_data["high"],
                            "low": ticker_data["low"],
                            "opportunity_type": "momentum" if pct_change > 0 else "reversal"
                        })
                        
            # Sort by absolute price change
            opportunities.sort(key=lambda x: abs(x["price_change"]), reverse=True)
            
            return opportunities[:20]  # Return top 20 opportunities
            
        except Exception as e:
            logger.error(f"Error scanning for opportunities: {e}")
            return []


# Singleton instance
polygon_service = PolygonService()