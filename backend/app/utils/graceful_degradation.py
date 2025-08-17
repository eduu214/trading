"""
Graceful degradation strategies for service failures
"""
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
import asyncio
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ServiceLevel(Enum):
    FULL = "full"              # All services available
    DEGRADED = "degraded"      # Some services unavailable
    MINIMAL = "minimal"        # Core functionality only
    OFFLINE = "offline"        # No external services

class FallbackStrategy(Enum):
    CACHE_ONLY = "cache_only"
    MOCK_DATA = "mock_data"
    REDUCED_SCOPE = "reduced_scope"
    SKIP_FEATURE = "skip_feature"
    MANUAL_MODE = "manual_mode"

class ServiceDependency:
    """Represents a service dependency with fallback options"""
    
    def __init__(self,
                 name: str,
                 criticality: str,  # "critical", "important", "optional"
                 fallback_strategy: FallbackStrategy,
                 fallback_data: Any = None):
        self.name = name
        self.criticality = criticality
        self.fallback_strategy = fallback_strategy
        self.fallback_data = fallback_data
        self.is_available = True
        self.last_failure = None
        self.failure_count = 0

class DegradationManager:
    """Manages service degradation and fallback strategies"""
    
    def __init__(self):
        self.service_level = ServiceLevel.FULL
        self.dependencies: Dict[str, ServiceDependency] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.cached_data: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        self._setup_default_dependencies()
    
    def _setup_default_dependencies(self):
        """Setup default service dependencies"""
        self.register_dependency(
            "polygon",
            "critical",
            FallbackStrategy.MOCK_DATA,
            self._get_mock_market_data()
        )
        
        self.register_dependency(
            "alpaca",
            "important",
            FallbackStrategy.CACHE_ONLY
        )
        
        self.register_dependency(
            "redis",
            "important",
            FallbackStrategy.MANUAL_MODE
        )
        
        self.register_dependency(
            "database",
            "critical",
            FallbackStrategy.CACHE_ONLY
        )
    
    def register_dependency(self,
                          name: str,
                          criticality: str,
                          fallback_strategy: FallbackStrategy,
                          fallback_data: Any = None):
        """Register a service dependency"""
        self.dependencies[name] = ServiceDependency(
            name, criticality, fallback_strategy, fallback_data
        )
    
    def register_fallback_handler(self, service: str, handler: Callable):
        """Register custom fallback handler for a service"""
        self.fallback_handlers[service] = handler
    
    def mark_service_down(self, service: str, error: str = None):
        """Mark a service as unavailable"""
        if service in self.dependencies:
            dep = self.dependencies[service]
            dep.is_available = False
            dep.last_failure = datetime.now()
            dep.failure_count += 1
            
            logger.warning(
                f"Service {service} marked as down. "
                f"Failure count: {dep.failure_count}. Error: {error}"
            )
            
            self._reassess_service_level()
    
    def mark_service_up(self, service: str):
        """Mark a service as available"""
        if service in self.dependencies:
            dep = self.dependencies[service]
            if not dep.is_available:
                logger.info(f"Service {service} restored")
            
            dep.is_available = True
            dep.failure_count = 0
            dep.last_failure = None
            
            self._reassess_service_level()
    
    def _reassess_service_level(self):
        """Reassess overall service level based on dependencies"""
        critical_down = []
        important_down = []
        
        for service, dep in self.dependencies.items():
            if not dep.is_available:
                if dep.criticality == "critical":
                    critical_down.append(service)
                elif dep.criticality == "important":
                    important_down.append(service)
        
        old_level = self.service_level
        
        if critical_down:
            if len(critical_down) > 1:
                self.service_level = ServiceLevel.OFFLINE
            else:
                self.service_level = ServiceLevel.MINIMAL
        elif important_down:
            self.service_level = ServiceLevel.DEGRADED
        else:
            self.service_level = ServiceLevel.FULL
        
        if old_level != self.service_level:
            logger.info(f"Service level changed: {old_level.value} → {self.service_level.value}")
    
    async def execute_with_fallback(self,
                                  service: str,
                                  primary_func: Callable,
                                  *args,
                                  use_cache: bool = True,
                                  cache_ttl: int = 300,  # 5 minutes
                                  **kwargs) -> Any:
        """
        Execute function with fallback handling
        
        Args:
            service: Service name
            primary_func: Primary function to execute
            use_cache: Whether to use cached results
            cache_ttl: Cache time-to-live in seconds
        """
        cache_key = f"{service}_{primary_func.__name__}_{str(args)}_{str(kwargs)}"
        
        # Check cache first if enabled
        if use_cache and cache_key in self.cached_data:
            cache_time = self.cache_timestamps.get(cache_key)
            if cache_time and (datetime.now() - cache_time).seconds < cache_ttl:
                logger.debug(f"Using cached data for {service}")
                return self.cached_data[cache_key]
        
        # Try primary function
        try:
            result = await primary_func(*args, **kwargs)
            
            # Cache successful result
            if use_cache:
                self.cached_data[cache_key] = result
                self.cache_timestamps[cache_key] = datetime.now()
            
            # Mark service as up
            self.mark_service_up(service)
            
            return result
            
        except Exception as e:
            logger.error(f"Primary function failed for {service}: {e}")
            self.mark_service_down(service, str(e))
            
            # Try fallback
            return await self._execute_fallback(service, cache_key, *args, **kwargs)
    
    async def _execute_fallback(self, service: str, cache_key: str, *args, **kwargs) -> Any:
        """Execute fallback strategy for a service"""
        if service not in self.dependencies:
            raise Exception(f"No fallback strategy for service: {service}")
        
        dep = self.dependencies[service]
        strategy = dep.fallback_strategy
        
        logger.info(f"Executing fallback strategy {strategy.value} for {service}")
        
        if strategy == FallbackStrategy.CACHE_ONLY:
            if cache_key in self.cached_data:
                logger.info(f"Using stale cached data for {service}")
                return self.cached_data[cache_key]
            else:
                raise Exception(f"No cached data available for {service}")
        
        elif strategy == FallbackStrategy.MOCK_DATA:
            if service in self.fallback_handlers:
                return await self.fallback_handlers[service](*args, **kwargs)
            elif dep.fallback_data:
                return dep.fallback_data
            else:
                return self._get_default_mock_data(service)
        
        elif strategy == FallbackStrategy.REDUCED_SCOPE:
            # Return limited/filtered results
            return await self._reduced_scope_fallback(service, *args, **kwargs)
        
        elif strategy == FallbackStrategy.SKIP_FEATURE:
            logger.warning(f"Skipping feature due to {service} unavailability")
            return None
        
        elif strategy == FallbackStrategy.MANUAL_MODE:
            logger.warning(f"Manual intervention required for {service}")
            return {"status": "manual_mode", "service": service}
        
        else:
            raise Exception(f"Unknown fallback strategy: {strategy}")
    
    def _get_mock_market_data(self) -> Dict:
        """Generate mock market data for testing"""
        return {
            "opportunities": [
                {
                    "ticker": "MOCK_EQUITY",
                    "asset_class": "equities",
                    "opportunity_type": "price_deviation",
                    "signal_strength": 75.0,
                    "entry_price": 100.0,
                    "price_change": 0.025,
                    "volume": 1000000,
                    "inefficiency_score": 0.8,
                    "discovered_at": datetime.now().isoformat(),
                    "spread": 0.01
                }
            ],
            "status": "mock_data",
            "opportunities_found": 1
        }
    
    def _get_default_mock_data(self, service: str) -> Any:
        """Get default mock data for a service"""
        mock_data = {
            "polygon": self._get_mock_market_data(),
            "alpaca": {"account": {"equity": 100000, "buying_power": 50000}},
            "redis": {"status": "mock"},
            "database": {"status": "mock", "data": []}
        }
        return mock_data.get(service, {"status": "mock", "service": service})
    
    async def _reduced_scope_fallback(self, service: str, *args, **kwargs) -> Any:
        """Implement reduced scope fallback"""
        if service == "polygon":
            # Return limited market data
            return {
                "opportunities": [],
                "status": "reduced_scope",
                "message": "Limited data due to service unavailability"
            }
        elif service == "alpaca":
            # Return basic account info
            return {
                "account": {"status": "limited"},
                "message": "Limited functionality"
            }
        else:
            return {"status": "reduced_scope", "service": service}
    
    def get_service_status(self) -> Dict:
        """Get current service status"""
        return {
            "service_level": self.service_level.value,
            "dependencies": {
                name: {
                    "available": dep.is_available,
                    "criticality": dep.criticality,
                    "failure_count": dep.failure_count,
                    "last_failure": dep.last_failure.isoformat() if dep.last_failure else None,
                    "fallback_strategy": dep.fallback_strategy.value
                }
                for name, dep in self.dependencies.items()
            }
        }
    
    def get_degradation_info(self) -> Dict:
        """Get information about current degradation"""
        unavailable_services = [
            name for name, dep in self.dependencies.items()
            if not dep.is_available
        ]
        
        return {
            "service_level": self.service_level.value,
            "unavailable_services": unavailable_services,
            "capabilities": self._get_available_capabilities(),
            "recommendations": self._get_user_recommendations()
        }
    
    def _get_available_capabilities(self) -> List[str]:
        """Get list of currently available capabilities"""
        capabilities = []
        
        if self.service_level == ServiceLevel.FULL:
            capabilities = [
                "Full market scanning",
                "Real-time data",
                "All asset classes",
                "Complete analysis",
                "Trading execution"
            ]
        elif self.service_level == ServiceLevel.DEGRADED:
            capabilities = [
                "Limited market scanning",
                "Cached data",
                "Basic analysis",
                "Reduced asset classes"
            ]
        elif self.service_level == ServiceLevel.MINIMAL:
            capabilities = [
                "Mock data scanning",
                "Offline analysis",
                "Basic functionality"
            ]
        else:  # OFFLINE
            capabilities = [
                "Cached data only",
                "No real-time updates",
                "Manual operation required"
            ]
        
        return capabilities
    
    def _get_user_recommendations(self) -> List[str]:
        """Get recommendations for users during degradation"""
        recommendations = []
        
        if self.service_level != ServiceLevel.FULL:
            recommendations.append("Some features may be limited")
            
        if not self.dependencies.get("polygon", ServiceDependency("", "", FallbackStrategy.MOCK_DATA)).is_available:
            recommendations.append("Market data may be delayed or mock data")
            
        if not self.dependencies.get("alpaca", ServiceDependency("", "", FallbackStrategy.CACHE_ONLY)).is_available:
            recommendations.append("Trading functionality is limited")
            
        if self.service_level == ServiceLevel.OFFLINE:
            recommendations.append("System is in offline mode - manual intervention may be required")
        
        return recommendations

# Global degradation manager
degradation_manager = DegradationManager()