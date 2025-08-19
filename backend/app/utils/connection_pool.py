"""
High-performance connection pooling for database and external APIs
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, AsyncContextManager
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
import aiohttp
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    """Statistics for a connection pool"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    closed_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    avg_acquisition_time: float = 0
    max_acquisition_time: float = 0

class DatabaseConnectionPool:
    """High-performance database connection pool"""
    
    def __init__(self, 
                 database_url: str,
                 min_size: int = 5,
                 max_size: int = 20,
                 max_idle_time: int = 300,  # 5 minutes
                 acquire_timeout: float = 30.0):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.acquire_timeout = acquire_timeout
        
        # SQLAlchemy async engine with optimized settings
        self.engine = create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=min_size,
            max_overflow=max_size - min_size,
            pool_timeout=acquire_timeout,
            pool_recycle=3600,  # Recycle connections every hour
            pool_pre_ping=True,  # Validate connections before use
            echo=False  # Set to True for SQL logging in development
        )
        
        self.stats = ConnectionStats()
        self._acquisition_times = []
    
    async def initialize(self):
        """Initialize the connection pool"""
        try:
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info(f"Database connection pool initialized: {self.min_size}-{self.max_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        start_time = time.time()
        
        try:
            async with self.engine.begin() as conn:
                acquisition_time = time.time() - start_time
                self._track_acquisition(acquisition_time)
                
                self.stats.active_connections += 1
                self.stats.total_requests += 1
                
                try:
                    yield conn
                finally:
                    self.stats.active_connections -= 1
                    
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Database connection error: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get SQLAlchemy async session"""
        start_time = time.time()
        
        try:
            async with AsyncSession(self.engine) as session:
                acquisition_time = time.time() - start_time
                self._track_acquisition(acquisition_time)
                
                self.stats.active_connections += 1
                self.stats.total_requests += 1
                
                try:
                    yield session
                finally:
                    self.stats.active_connections -= 1
                    
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Database session error: {e}")
            raise
    
    def _track_acquisition(self, acquisition_time: float):
        """Track connection acquisition metrics"""
        self._acquisition_times.append(acquisition_time)
        
        # Keep only recent acquisition times (last 1000)
        if len(self._acquisition_times) > 1000:
            self._acquisition_times = self._acquisition_times[-1000:]
        
        # Update stats
        self.stats.avg_acquisition_time = sum(self._acquisition_times) / len(self._acquisition_times)
        self.stats.max_acquisition_time = max(self._acquisition_times)
    
    async def close(self):
        """Close the connection pool"""
        await self.engine.dispose()
        logger.info("Database connection pool closed")
    
    def get_stats(self) -> Dict:
        """Get connection pool statistics"""
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "stats": {
                "total_requests": self.stats.total_requests,
                "active_connections": self.stats.active_connections,
                "failed_connections": self.stats.failed_connections,
                "avg_acquisition_time_ms": self.stats.avg_acquisition_time * 1000,
                "max_acquisition_time_ms": self.stats.max_acquisition_time * 1000
            }
        }

class HTTPConnectionPool:
    """HTTP connection pool for external APIs"""
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_keepalive_connections: int = 20,
                 keepalive_expiry: float = 30.0,
                 timeout: float = 30.0):
        
        # Configure connection limits
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_keepalive_connections,
            keepalive_timeout=keepalive_expiry,
            enable_cleanup_closed=True
        )
        
        # Configure timeout
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        
        # Create session
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers={
                'User-Agent': 'AlphaStrat/1.0',
                'Accept': 'application/json'
            }
        )
        
        self.stats = ConnectionStats()
        self._request_times = []
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request"""
        return await self._request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request"""
        return await self._request('POST', url, **kwargs)
    
    async def _request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with statistics tracking"""
        start_time = time.time()
        
        try:
            response = await self.session.request(method, url, **kwargs)
            
            request_time = time.time() - start_time
            self._track_request(request_time, True)
            
            return response
            
        except Exception as e:
            request_time = time.time() - start_time
            self._track_request(request_time, False)
            
            logger.error(f"HTTP request failed: {method} {url} - {e}")
            raise
    
    def _track_request(self, request_time: float, success: bool):
        """Track request metrics"""
        self._request_times.append(request_time)
        
        # Keep only recent request times
        if len(self._request_times) > 1000:
            self._request_times = self._request_times[-1000:]
        
        # Update stats
        self.stats.total_requests += 1
        if not success:
            self.stats.failed_connections += 1
        
        if self._request_times:
            self.stats.avg_acquisition_time = sum(self._request_times) / len(self._request_times)
            self.stats.max_acquisition_time = max(self._request_times)
    
    async def close(self):
        """Close HTTP session"""
        await self.session.close()
        logger.info("HTTP connection pool closed")
    
    def get_stats(self) -> Dict:
        """Get HTTP pool statistics"""
        connector_info = {}
        if hasattr(self.session.connector, '_conns'):
            # Try to get connector statistics
            try:
                total_conns = sum(len(conns) for conns in self.session.connector._conns.values())
                connector_info = {
                    "total_connections": total_conns,
                    "connection_limit": self.session.connector.limit,
                    "per_host_limit": self.session.connector.limit_per_host
                }
            except:
                connector_info = {"status": "statistics_unavailable"}
        
        return {
            "connector": connector_info,
            "stats": {
                "total_requests": self.stats.total_requests,
                "failed_requests": self.stats.failed_connections,
                "avg_request_time_ms": self.stats.avg_acquisition_time * 1000,
                "max_request_time_ms": self.stats.max_acquisition_time * 1000
            }
        }

class PolygonConnectionPool(HTTPConnectionPool):
    """Specialized connection pool for Polygon.io API"""
    
    def __init__(self, api_key: str):
        super().__init__(
            max_connections=20,  # Polygon rate limits
            max_keepalive_connections=5,
            timeout=30.0
        )
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        
        # Update session headers
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
    
    async def get_tickers(self, **params) -> Dict:
        """Get ticker data from Polygon"""
        url = f"{self.base_url}/v3/reference/tickers"
        
        async with await self.get(url, params=params) as response:
            return await response.json()
    
    async def get_aggregates(self, ticker: str, timespan: str, multiplier: int,
                           from_date: str, to_date: str) -> Dict:
        """Get aggregate data from Polygon"""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        async with await self.get(url) as response:
            return await response.json()
    
    async def get_last_trade(self, ticker: str) -> Dict:
        """Get last trade for ticker"""
        url = f"{self.base_url}/v2/last/trade/{ticker}"
        
        async with await self.get(url) as response:
            return await response.json()

class AlpacaConnectionPool(HTTPConnectionPool):
    """Specialized connection pool for Alpaca API"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        super().__init__(
            max_connections=50,  # Alpaca allows more connections
            max_keepalive_connections=10,
            timeout=30.0
        )
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        
        # Update session headers
        self.session.headers.update({
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key
        })
    
    async def get_account(self) -> Dict:
        """Get account information"""
        url = f"{self.base_url}/v2/account"
        
        async with await self.get(url) as response:
            return await response.json()
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        url = f"{self.base_url}/v2/positions"
        
        async with await self.get(url) as response:
            return await response.json()
    
    async def place_order(self, order_data: Dict) -> Dict:
        """Place trading order"""
        url = f"{self.base_url}/v2/orders"
        
        async with await self.post(url, json=order_data) as response:
            return await response.json()

class ConnectionPoolManager:
    """Manage multiple connection pools"""
    
    def __init__(self):
        self.pools: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize(self, config: Dict):
        """Initialize all connection pools"""
        if self.initialized:
            return
        
        try:
            # Initialize database pool
            if 'database_url' in config:
                db_pool = DatabaseConnectionPool(
                    database_url=config['database_url'],
                    min_size=config.get('db_min_connections', 5),
                    max_size=config.get('db_max_connections', 20)
                )
                await db_pool.initialize()
                self.pools['database'] = db_pool
            
            # Initialize Polygon pool
            if 'polygon_api_key' in config:
                polygon_pool = PolygonConnectionPool(config['polygon_api_key'])
                self.pools['polygon'] = polygon_pool
            
            # Initialize Alpaca pool
            if 'alpaca_api_key' in config and 'alpaca_secret_key' in config:
                alpaca_pool = AlpacaConnectionPool(
                    api_key=config['alpaca_api_key'],
                    secret_key=config['alpaca_secret_key'],
                    paper=config.get('alpaca_paper', True)
                )
                self.pools['alpaca'] = alpaca_pool
            
            # Initialize general HTTP pool
            http_pool = HTTPConnectionPool()
            self.pools['http'] = http_pool
            
            self.initialized = True
            logger.info(f"Initialized {len(self.pools)} connection pools")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    def get_pool(self, pool_name: str) -> Optional[Any]:
        """Get specific connection pool"""
        return self.pools.get(pool_name)
    
    async def close_all(self):
        """Close all connection pools"""
        for name, pool in self.pools.items():
            try:
                await pool.close()
                logger.info(f"Closed connection pool: {name}")
            except Exception as e:
                logger.error(f"Error closing pool {name}: {e}")
        
        self.pools.clear()
        self.initialized = False
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all pools"""
        stats = {}
        
        for name, pool in self.pools.items():
            try:
                stats[name] = pool.get_stats()
            except Exception as e:
                stats[name] = {"error": str(e)}
        
        return stats
    
    async def health_check(self) -> Dict:
        """Perform health check on all pools"""
        results = {}
        
        for name, pool in self.pools.items():
            try:
                if name == 'database' and hasattr(pool, 'get_connection'):
                    # Test database connection
                    async with pool.get_connection() as conn:
                        await conn.execute("SELECT 1")
                    results[name] = {"status": "healthy", "error": None}
                
                elif hasattr(pool, 'get'):
                    # Test HTTP pools with a simple request
                    if name == 'polygon':
                        # Test Polygon connection
                        async with await pool.get(f"{pool.base_url}/v1/meta/exchanges") as response:
                            results[name] = {
                                "status": "healthy" if response.status in [200, 401] else "unhealthy",
                                "status_code": response.status,
                                "error": None
                            }
                    elif name == 'alpaca':
                        # Test Alpaca connection
                        try:
                            async with await pool.get(f"{pool.base_url}/v2/clock") as response:
                                results[name] = {
                                    "status": "healthy" if response.status in [200, 401] else "unhealthy",
                                    "status_code": response.status,
                                    "error": None
                                }
                        except Exception as e:
                            results[name] = {"status": "unhealthy", "error": str(e)}
                    else:
                        results[name] = {"status": "healthy", "error": None}
                        
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
        
        return results

# Global connection pool manager
pool_manager = ConnectionPoolManager()

# Convenience functions
@asynccontextmanager
async def get_db_session():
    """Get database session from global pool"""
    db_pool = pool_manager.get_pool('database')
    if not db_pool:
        raise RuntimeError("Database pool not initialized")
    
    async with db_pool.get_session() as session:
        yield session

@asynccontextmanager
async def get_db_connection():
    """Get database connection from global pool"""
    db_pool = pool_manager.get_pool('database')
    if not db_pool:
        raise RuntimeError("Database pool not initialized")
    
    async with db_pool.get_connection() as conn:
        yield conn

def get_polygon_pool() -> Optional[PolygonConnectionPool]:
    """Get Polygon connection pool"""
    return pool_manager.get_pool('polygon')

def get_alpaca_pool() -> Optional[AlpacaConnectionPool]:
    """Get Alpaca connection pool"""
    return pool_manager.get_pool('alpaca')

def get_http_pool() -> Optional[HTTPConnectionPool]:
    """Get general HTTP connection pool"""
    return pool_manager.get_pool('http')