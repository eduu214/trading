"""
Network connectivity monitoring and health checks
"""
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceHealth:
    """Health status for a service"""
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.status = ServiceStatus.UNKNOWN
        self.last_check = None
        self.last_success = None
        self.consecutive_failures = 0
        self.response_times = []
        self.average_response_time = 0
        
    def record_success(self, response_time: float):
        """Record successful health check"""
        self.status = ServiceStatus.HEALTHY
        self.last_check = datetime.now()
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        
        # Track response times (keep last 100)
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        
        self.average_response_time = sum(self.response_times) / len(self.response_times)
        
        # Check if degraded (slow response)
        if response_time > 5.0:  # 5 seconds is considered slow
            self.status = ServiceStatus.DEGRADED
    
    def record_failure(self, error: str):
        """Record failed health check"""
        self.last_check = datetime.now()
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= 3:
            self.status = ServiceStatus.UNHEALTHY
        elif self.consecutive_failures >= 1:
            self.status = ServiceStatus.DEGRADED
        
        logger.warning(
            f"Health check failed for {self.name}: {error}. "
            f"Consecutive failures: {self.consecutive_failures}"
        )
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return self.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]

class NetworkMonitor:
    """
    Monitor network connectivity and service health
    """
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.services: Dict[str, ServiceHealth] = {}
        self.monitoring = False
        self.callbacks: List[Callable] = []
        
        # Add default services to monitor
        self._add_default_services()
    
    def _add_default_services(self):
        """Add default services to monitor"""
        default_services = [
            ("polygon", "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-01/2023-01-01"),
            ("alpaca", "https://paper-api.alpaca.markets/v2/account"),
            ("internet", "https://www.google.com"),
            ("dns", "https://8.8.8.8"),
        ]
        
        for name, url in default_services:
            self.add_service(name, url)
    
    def add_service(self, name: str, url: str):
        """Add a service to monitor"""
        self.services[name] = ServiceHealth(name, url)
    
    def add_callback(self, callback: Callable):
        """Add callback for status changes"""
        self.callbacks.append(callback)
    
    async def check_service(self, service: ServiceHealth) -> bool:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    service.url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status < 500:
                        service.record_success(response_time)
                        return True
                    else:
                        service.record_failure(f"HTTP {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            service.record_failure("Timeout")
            return False
        except aiohttp.ClientError as e:
            service.record_failure(str(e))
            return False
        except Exception as e:
            service.record_failure(f"Unknown error: {e}")
            return False
    
    async def check_all_services(self):
        """Check health of all services"""
        tasks = []
        for service in self.services.values():
            tasks.append(self.check_service(service))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Notify callbacks of any status changes
        for callback in self.callbacks:
            try:
                await callback(self.get_status())
            except Exception as e:
                logger.error(f"Error in health check callback: {e}")
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            await self.check_all_services()
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def get_status(self) -> Dict:
        """Get current status of all services"""
        return {
            name: {
                "status": service.status.value,
                "last_check": service.last_check.isoformat() if service.last_check else None,
                "last_success": service.last_success.isoformat() if service.last_success else None,
                "consecutive_failures": service.consecutive_failures,
                "average_response_time": round(service.average_response_time, 3),
                "available": service.is_available()
            }
            for name, service in self.services.items()
        }
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if specific service is available"""
        if service_name in self.services:
            return self.services[service_name].is_available()
        return False
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get status of specific service"""
        if service_name in self.services:
            return self.services[service_name].status
        return ServiceStatus.UNKNOWN
    
    async def wait_for_service(self, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if service_name in self.services:
                await self.check_service(self.services[service_name])
                if self.services[service_name].is_available():
                    return True
            
            await asyncio.sleep(5)
        
        return False

class ConnectivityChecker:
    """
    Quick connectivity checks for critical operations
    """
    @staticmethod
    async def check_internet() -> bool:
        """Quick internet connectivity check"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.google.com",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    @staticmethod
    async def check_polygon() -> bool:
        """Quick Polygon.io connectivity check"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.polygon.io/v1/meta/exchanges",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status in [200, 401]  # 401 means connected but need auth
        except:
            return False
    
    @staticmethod
    async def check_alpaca() -> bool:
        """Quick Alpaca connectivity check"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://paper-api.alpaca.markets/v2/clock",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status in [200, 401]
        except:
            return False
    
    @staticmethod
    async def check_all() -> Dict[str, bool]:
        """Check all critical services"""
        results = await asyncio.gather(
            ConnectivityChecker.check_internet(),
            ConnectivityChecker.check_polygon(),
            ConnectivityChecker.check_alpaca(),
            return_exceptions=True
        )
        
        return {
            "internet": results[0] if not isinstance(results[0], Exception) else False,
            "polygon": results[1] if not isinstance(results[1], Exception) else False,
            "alpaca": results[2] if not isinstance(results[2], Exception) else False,
        }

# Global network monitor instance
network_monitor = NetworkMonitor()

async def ensure_connectivity(services: List[str] = None) -> bool:
    """
    Ensure required services are available before proceeding
    
    Args:
        services: List of service names to check. If None, checks all.
    
    Returns:
        True if all required services are available
    """
    if services is None:
        services = ["internet", "polygon", "alpaca"]
    
    # Quick connectivity check first
    quick_check = await ConnectivityChecker.check_all()
    
    for service in services:
        if service in quick_check and not quick_check[service]:
            logger.error(f"Service {service} is not available")
            return False
    
    return True