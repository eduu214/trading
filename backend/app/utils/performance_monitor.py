"""
Performance monitoring and alerting system for the AlphaStrat trading platform
"""
import asyncio
import time
import psutil
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import deque

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"

@dataclass
class Metric:
    """Represents a performance metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class Alert:
    """Represents a performance alert"""
    id: str
    severity: AlertSeverity
    message: str
    metric_name: str
    threshold: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None

@dataclass
class PerformanceThreshold:
    """Performance monitoring threshold"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    operator: str = ">"  # >, <, >=, <=, ==
    duration_seconds: int = 60  # Alert if threshold exceeded for this duration
    enabled: bool = True

class MetricsCollector:
    """Collect and store performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.metric_aggregates: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def add_metric(self, metric: Metric):
        """Add a metric to the collection"""
        with self._lock:
            self.metrics.append(metric)
            self._update_aggregates(metric)
    
    def add_counter(self, name: str, value: float = 1, tags: Dict = None):
        """Add a counter metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            tags=tags or {},
            unit="count"
        )
        self.add_metric(metric)
    
    def add_gauge(self, name: str, value: float, unit: str = "", tags: Dict = None):
        """Add a gauge metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            tags=tags or {},
            unit=unit
        )
        self.add_metric(metric)
    
    def add_histogram(self, name: str, value: float, unit: str = "", tags: Dict = None):
        """Add a histogram metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            tags=tags or {},
            unit=unit
        )
        self.add_metric(metric)
    
    def add_rate(self, name: str, value: float, unit: str = "per_second", tags: Dict = None):
        """Add a rate metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.RATE,
            tags=tags or {},
            unit=unit
        )
        self.add_metric(metric)
    
    def _update_aggregates(self, metric: Metric):
        """Update metric aggregates"""
        name = metric.name
        
        if name not in self.metric_aggregates:
            self.metric_aggregates[name] = {
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "last_value": 0,
                "last_timestamp": None
            }
        
        agg = self.metric_aggregates[name]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["last_value"] = metric.value
        agg["last_timestamp"] = metric.timestamp
    
    def get_metrics(self, 
                   name_filter: str = None,
                   since: datetime = None,
                   limit: int = None) -> List[Metric]:
        """Get metrics with optional filtering"""
        with self._lock:
            metrics = list(self.metrics)
        
        # Apply filters
        if name_filter:
            metrics = [m for m in metrics if name_filter in m.name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        # Sort by timestamp (newest first)
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        
        if limit:
            metrics = metrics[:limit]
        
        return metrics
    
    def get_aggregates(self, name: str = None) -> Dict:
        """Get metric aggregates"""
        with self._lock:
            if name:
                return self.metric_aggregates.get(name, {})
            else:
                return self.metric_aggregates.copy()

class SystemMetricsCollector:
    """Collect system-level performance metrics"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.process = psutil.Process()
        self.collecting = False
        self.collection_task = None
    
    async def start_collection(self, interval: float = 30.0):
        """Start collecting system metrics"""
        if self.collecting:
            return
        
        self.collecting = True
        self.collection_task = asyncio.create_task(
            self._collect_metrics_loop(interval)
        )
        logger.info(f"Started system metrics collection (interval: {interval}s)")
    
    async def stop_collection(self):
        """Stop collecting system metrics"""
        self.collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped system metrics collection")
    
    async def _collect_metrics_loop(self, interval: float):
        """Main metrics collection loop"""
        while self.collecting:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.collector.add_gauge("system.cpu.usage", cpu_percent, "percent")
        
        cpu_count = psutil.cpu_count()
        self.collector.add_gauge("system.cpu.count", cpu_count, "cores")
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.collector.add_gauge("system.memory.total", memory.total / (1024**3), "GB")
        self.collector.add_gauge("system.memory.available", memory.available / (1024**3), "GB")
        self.collector.add_gauge("system.memory.used", memory.used / (1024**3), "GB")
        self.collector.add_gauge("system.memory.usage", memory.percent, "percent")
        
        # Process metrics
        try:
            process_memory = self.process.memory_info()
            self.collector.add_gauge("process.memory.rss", process_memory.rss / (1024**2), "MB")
            self.collector.add_gauge("process.memory.vms", process_memory.vms / (1024**2), "MB")
            
            process_cpu = self.process.cpu_percent()
            self.collector.add_gauge("process.cpu.usage", process_cpu, "percent")
            
            # Thread count
            thread_count = self.process.num_threads()
            self.collector.add_gauge("process.threads", thread_count, "count")
            
            # File descriptors (Unix only)
            try:
                fd_count = self.process.num_fds()
                self.collector.add_gauge("process.file_descriptors", fd_count, "count")
            except (AttributeError, psutil.AccessDenied):
                pass
                
        except psutil.NoSuchProcess:
            logger.warning("Process no longer exists")
        
        # Disk metrics
        try:
            disk = psutil.disk_usage('/')
            self.collector.add_gauge("system.disk.total", disk.total / (1024**3), "GB")
            self.collector.add_gauge("system.disk.used", disk.used / (1024**3), "GB")
            self.collector.add_gauge("system.disk.free", disk.free / (1024**3), "GB")
            self.collector.add_gauge("system.disk.usage", (disk.used / disk.total) * 100, "percent")
        except:
            pass

class AlertManager:
    """Manage performance alerts and notifications"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable] = []
        self.monitoring = False
        self.monitor_task = None
        
        # Setup default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds"""
        default_thresholds = [
            PerformanceThreshold("system.cpu.usage", 80.0, 95.0, ">", 60),
            PerformanceThreshold("system.memory.usage", 80.0, 95.0, ">", 60),
            PerformanceThreshold("process.memory.rss", 1000.0, 2000.0, ">", 60),  # MB
            PerformanceThreshold("system.disk.usage", 85.0, 95.0, ">", 300),
            PerformanceThreshold("api.response_time", 1000.0, 5000.0, ">", 30),  # ms
            PerformanceThreshold("database.query_time", 1000.0, 5000.0, ">", 30),  # ms
        ]
        
        for threshold in default_thresholds:
            self.add_threshold(threshold)
    
    def add_threshold(self, threshold: PerformanceThreshold):
        """Add performance threshold"""
        self.thresholds[threshold.metric_name] = threshold
        logger.info(f"Added threshold for {threshold.metric_name}")
    
    def remove_threshold(self, metric_name: str):
        """Remove performance threshold"""
        if metric_name in self.thresholds:
            del self.thresholds[metric_name]
            logger.info(f"Removed threshold for {metric_name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self, check_interval: float = 30.0):
        """Start alert monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(
            self._monitor_loop(check_interval)
        )
        logger.info(f"Started alert monitoring (interval: {check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop alert monitoring"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped alert monitoring")
    
    async def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self._check_thresholds()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _check_thresholds(self):
        """Check all thresholds against current metrics"""
        aggregates = self.collector.get_aggregates()
        
        for metric_name, threshold in self.thresholds.items():
            if not threshold.enabled:
                continue
            
            if metric_name not in aggregates:
                continue
            
            current_value = aggregates[metric_name]["last_value"]
            last_timestamp = aggregates[metric_name]["last_timestamp"]
            
            # Check if metric is recent enough
            if last_timestamp and (datetime.now() - last_timestamp).seconds > 300:
                continue  # Skip stale metrics
            
            # Check thresholds
            await self._check_metric_threshold(
                metric_name, current_value, threshold
            )
    
    async def _check_metric_threshold(self, 
                                    metric_name: str,
                                    current_value: float,
                                    threshold: PerformanceThreshold):
        """Check specific metric against threshold"""
        # Evaluate threshold condition
        exceeds_warning = self._evaluate_condition(
            current_value, threshold.warning_threshold, threshold.operator
        )
        exceeds_critical = self._evaluate_condition(
            current_value, threshold.critical_threshold, threshold.operator
        )
        
        alert_id = f"{metric_name}_alert"
        
        if exceeds_critical:
            # Critical alert
            if alert_id not in self.active_alerts:
                alert = Alert(
                    id=alert_id,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Critical threshold exceeded for {metric_name}",
                    metric_name=metric_name,
                    threshold=threshold.critical_threshold,
                    current_value=current_value
                )
                
                await self._trigger_alert(alert)
        
        elif exceeds_warning:
            # Warning alert
            if alert_id not in self.active_alerts:
                alert = Alert(
                    id=alert_id,
                    severity=AlertSeverity.HIGH,
                    message=f"Warning threshold exceeded for {metric_name}",
                    metric_name=metric_name,
                    threshold=threshold.warning_threshold,
                    current_value=current_value
                )
                
                await self._trigger_alert(alert)
        
        else:
            # Check if we should resolve existing alert
            if alert_id in self.active_alerts:
                await self._resolve_alert(alert_id)
    
    def _evaluate_condition(self, value: float, threshold: float, operator: str) -> bool:
        """Evaluate threshold condition"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        else:
            return False
    
    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        logger.warning(
            f"ALERT [{alert.severity.value.upper()}]: {alert.message} "
            f"(Current: {alert.current_value}, Threshold: {alert.threshold})"
        )
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    async def _resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            
            del self.active_alerts[alert_id]
            
            logger.info(f"RESOLVED: Alert {alert_id}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff
        ]

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.system_collector = SystemMetricsCollector(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.running = False
    
    async def start(self, 
                   metrics_interval: float = 30.0,
                   alert_interval: float = 30.0):
        """Start performance monitoring"""
        if self.running:
            return
        
        self.running = True
        
        # Start components
        await self.system_collector.start_collection(metrics_interval)
        await self.alert_manager.start_monitoring(alert_interval)
        
        logger.info("Performance monitoring started")
    
    async def stop(self):
        """Stop performance monitoring"""
        self.running = False
        
        await self.system_collector.stop_collection()
        await self.alert_manager.stop_monitoring()
        
        logger.info("Performance monitoring stopped")
    
    def add_metric(self, name: str, value: float, 
                  metric_type: MetricType = MetricType.GAUGE,
                  unit: str = "", tags: Dict = None):
        """Add custom metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            unit=unit,
            tags=tags or {}
        )
        self.metrics_collector.add_metric(metric)
    
    def get_dashboard_data(self) -> Dict:
        """Get data for performance dashboard"""
        aggregates = self.metrics_collector.get_aggregates()
        active_alerts = self.alert_manager.get_active_alerts()
        recent_alerts = self.alert_manager.get_alert_history(hours=1)
        
        # System health summary
        cpu_usage = aggregates.get("system.cpu.usage", {}).get("last_value", 0)
        memory_usage = aggregates.get("system.memory.usage", {}).get("last_value", 0)
        disk_usage = aggregates.get("system.disk.usage", {}).get("last_value", 0)
        
        health_status = "healthy"
        if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
            health_status = "critical"
        elif cpu_usage > 70 or memory_usage > 70 or disk_usage > 70:
            health_status = "warning"
        
        return {
            "health_status": health_status,
            "system_metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "process_memory_mb": aggregates.get("process.memory.rss", {}).get("last_value", 0)
            },
            "alerts": {
                "active_count": len(active_alerts),
                "recent_count": len(recent_alerts),
                "active_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts
                ]
            },
            "metrics_summary": {
                "total_metrics": len(aggregates),
                "collection_running": self.running
            }
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()

# Decorator for timing functions
def monitor_performance(metric_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            name = metric_name or f"function.{func.__name__}.duration"
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to ms
                performance_monitor.add_metric(
                    name, duration, MetricType.HISTOGRAM, "ms",
                    {"success": str(success)}
                )
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            name = metric_name or f"function.{func.__name__}.duration"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                performance_monitor.add_metric(
                    name, duration, MetricType.HISTOGRAM, "ms",
                    {"success": str(success)}
                )
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator