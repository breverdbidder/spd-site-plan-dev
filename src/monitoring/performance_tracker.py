#!/usr/bin/env python3
"""
Performance Monitoring for SPD Site Plan Development
P2 Codebase Requirement: Performance tracking and optimization

Features:
- Request/response timing
- Pipeline stage metrics
- Memory and CPU tracking
- Slow query detection
- Real-time dashboards via Supabase
- Alerting thresholds

Author: BidDeed.AI / Everest Capital USA
"""

import os
import sys
import time
import json
import logging
import threading
import functools
from typing import Optional, Dict, Any, List, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import contextmanager
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MetricType(Enum):
    """Types of metrics tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


@dataclass
class AlertThreshold:
    """Threshold for metric alerts"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "gt"  # "gt", "lt", "eq"
    window_seconds: int = 60
    
    def check(self, value: float) -> Optional[str]:
        """Check if value exceeds threshold"""
        if self.comparison == "gt":
            if value > self.critical_threshold:
                return "critical"
            elif value > self.warning_threshold:
                return "warning"
        elif self.comparison == "lt":
            if value < self.critical_threshold:
                return "critical"
            elif value < self.warning_threshold:
                return "warning"
        return None


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, name: str, tracker: 'PerformanceTracker', tags: Optional[Dict] = None):
        self.name = name
        self.tracker = tracker
        self.tags = tags or {}
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        self.tracker.record_timer(self.name, duration_ms, self.tags)
        return False
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        if self.start_time is None:
            return 0
        end = self.end_time or time.perf_counter()
        return (end - self.start_time) * 1000


class PerformanceTracker:
    """
    Central performance tracking system.
    
    Usage:
        tracker = PerformanceTracker(module="bcpao_scraper")
        
        # Time a function
        @tracker.timed("scrape_parcel")
        def scrape_parcel(account_id):
            ...
        
        # Manual timing
        with tracker.timer("api_call", tags={"endpoint": "/search"}):
            response = requests.get(...)
        
        # Track metrics
        tracker.increment("parcels_scraped")
        tracker.gauge("queue_size", len(queue))
    """
    
    def __init__(
        self,
        module: str,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        flush_interval: int = 60,
        enable_memory_tracking: bool = True,
    ):
        self.module = module
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.flush_interval = flush_interval
        self.enable_memory_tracking = enable_memory_tracking
        
        # Metric storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Aggregated metrics buffer
        self._metrics_buffer: List[MetricPoint] = []
        self._buffer_lock = threading.Lock()
        
        # Alert thresholds
        self._thresholds: Dict[str, AlertThreshold] = {}
        
        # Start background flush thread
        self._stop_flush = threading.Event()
        self._flush_thread = threading.Thread(target=self._background_flush, daemon=True)
        self._flush_thread.start()
        
        # Setup default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds"""
        default_thresholds = [
            AlertThreshold("response_time_ms", 1000, 5000),
            AlertThreshold("error_rate", 0.05, 0.10),
            AlertThreshold("memory_mb", 512, 1024),
            AlertThreshold("queue_depth", 100, 500),
        ]
        for threshold in default_thresholds:
            self._thresholds[threshold.metric_name] = threshold
    
    def add_threshold(self, threshold: AlertThreshold):
        """Add a custom alert threshold"""
        self._thresholds[threshold.metric_name] = threshold
    
    # =========================================================================
    # METRIC RECORDING
    # =========================================================================
    
    def increment(self, name: str, value: float = 1, tags: Optional[Dict] = None):
        """Increment a counter metric"""
        full_name = f"{self.module}.{name}"
        self._counters[full_name] += value
        self._record_point(full_name, self._counters[full_name], MetricType.COUNTER, tags)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict] = None):
        """Set a gauge metric"""
        full_name = f"{self.module}.{name}"
        self._gauges[full_name] = value
        self._record_point(full_name, value, MetricType.GAUGE, tags)
        self._check_threshold(name, value)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict] = None):
        """Record a histogram value"""
        full_name = f"{self.module}.{name}"
        self._histograms[full_name].append(value)
        self._record_point(full_name, value, MetricType.HISTOGRAM, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict] = None):
        """Record a timer value"""
        full_name = f"{self.module}.{name}"
        self._timers[full_name].append(duration_ms)
        self._record_point(full_name, duration_ms, MetricType.TIMER, tags)
        self._check_threshold(f"{name}_ms", duration_ms)
    
    def _record_point(
        self, 
        name: str, 
        value: float, 
        metric_type: MetricType, 
        tags: Optional[Dict] = None
    ):
        """Record a metric point to buffer"""
        point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
        )
        
        with self._buffer_lock:
            self._metrics_buffer.append(point)
    
    def _check_threshold(self, name: str, value: float):
        """Check if value exceeds threshold and alert"""
        if name in self._thresholds:
            threshold = self._thresholds[name]
            alert_level = threshold.check(value)
            if alert_level:
                self._send_alert(name, value, alert_level, threshold)
    
    def _send_alert(
        self, 
        metric_name: str, 
        value: float, 
        level: str, 
        threshold: AlertThreshold
    ):
        """Send an alert for threshold violation"""
        message = (
            f"[{level.upper()}] {self.module}.{metric_name} = {value:.2f} "
            f"(threshold: {threshold.warning_threshold}/{threshold.critical_threshold})"
        )
        
        if level == "critical":
            logger.critical(message)
        else:
            logger.warning(message)
        
        # Could also send to external alerting system here
    
    # =========================================================================
    # TIMING HELPERS
    # =========================================================================
    
    def timer(self, name: str, tags: Optional[Dict] = None) -> Timer:
        """Create a timer context manager"""
        return Timer(name, self, tags)
    
    def timed(self, name: Optional[str] = None, tags: Optional[Dict] = None):
        """Decorator for timing functions"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            metric_name = name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                with self.timer(metric_name, tags):
                    return func(*args, **kwargs)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.record_timer(metric_name, duration_ms, tags)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        
        return decorator
    
    # =========================================================================
    # AGGREGATION & REPORTING
    # =========================================================================
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a timer"""
        full_name = f"{self.module}.{name}"
        values = self._timers.get(full_name, [])
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all performance statistics"""
        stats = {
            "module": self.module,
            "timestamp": datetime.utcnow().isoformat(),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timers": {},
        }
        
        for name in self._timers:
            short_name = name.replace(f"{self.module}.", "")
            stats["timers"][short_name] = self.get_timer_stats(short_name)
        
        # Add memory stats if enabled
        if self.enable_memory_tracking:
            stats["memory"] = self._get_memory_stats()
        
        return stats
    
    def _get_memory_stats(self) -> Dict[str, float]:
        """Get current memory statistics"""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            return {
                "rss_mb": mem_info.rss / 1024 / 1024,
                "vms_mb": mem_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
            }
        except ImportError:
            return {}
    
    # =========================================================================
    # DATA PERSISTENCE
    # =========================================================================
    
    def _background_flush(self):
        """Background thread for flushing metrics"""
        while not self._stop_flush.wait(self.flush_interval):
            self.flush()
    
    def flush(self):
        """Flush metrics buffer to storage"""
        with self._buffer_lock:
            if not self._metrics_buffer:
                return
            
            points_to_flush = self._metrics_buffer.copy()
            self._metrics_buffer.clear()
        
        # Aggregate points by minute
        aggregated = self._aggregate_points(points_to_flush)
        
        # Store to Supabase
        if self.supabase_url and self.supabase_key:
            self._store_metrics(aggregated)
    
    def _aggregate_points(self, points: List[MetricPoint]) -> List[Dict]:
        """Aggregate metric points by minute"""
        buckets = defaultdict(list)
        
        for point in points:
            # Create minute bucket key
            minute = point.timestamp.replace(second=0, microsecond=0)
            key = f"{point.name}:{minute.isoformat()}"
            buckets[key].append(point)
        
        aggregated = []
        for key, bucket_points in buckets.items():
            name, timestamp = key.rsplit(":", 1)
            values = [p.value for p in bucket_points]
            
            aggregated.append({
                "name": name,
                "timestamp": timestamp,
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "module": self.module,
            })
        
        return aggregated
    
    def _store_metrics(self, aggregated: List[Dict]):
        """Store aggregated metrics to Supabase"""
        try:
            import urllib.request
            
            for batch in [aggregated[i:i+100] for i in range(0, len(aggregated), 100)]:
                req = urllib.request.Request(
                    f"{self.supabase_url}/rest/v1/performance_metrics",
                    data=json.dumps(batch).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Prefer": "return=minimal",
                    },
                    method="POST"
                )
                
                urllib.request.urlopen(req, timeout=10)
            
            logger.debug(f"Flushed {len(aggregated)} metric aggregates")
        except Exception as e:
            logger.debug(f"Failed to store metrics: {e}")
    
    def stop(self):
        """Stop the background flush thread"""
        self._stop_flush.set()
        self._flush_thread.join(timeout=5)
        self.flush()  # Final flush


# =========================================================================
# PIPELINE-SPECIFIC TRACKING
# =========================================================================

class PipelinePerformanceTracker(PerformanceTracker):
    """Extended tracker for SPD pipeline stages"""
    
    def __init__(self, pipeline_id: str, **kwargs):
        super().__init__(module=f"pipeline.{pipeline_id}", **kwargs)
        self.pipeline_id = pipeline_id
        self._stage_timings: Dict[str, Dict] = {}
    
    @contextmanager
    def track_stage(self, stage_name: str, metadata: Optional[Dict] = None):
        """Context manager for tracking pipeline stage performance"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_stats().get("rss_mb", 0)
        
        self._stage_timings[stage_name] = {
            "start_time": datetime.utcnow().isoformat(),
            "status": "in_progress",
        }
        
        try:
            yield
            
            # Record success
            duration_ms = (time.perf_counter() - start_time) * 1000
            end_memory = self._get_memory_stats().get("rss_mb", 0)
            
            self._stage_timings[stage_name].update({
                "status": "completed",
                "duration_ms": duration_ms,
                "memory_delta_mb": end_memory - start_memory,
                "end_time": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            })
            
            self.record_timer(f"stage.{stage_name}", duration_ms)
            self.increment(f"stage.{stage_name}.success")
            
        except Exception as e:
            # Record failure
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            self._stage_timings[stage_name].update({
                "status": "failed",
                "duration_ms": duration_ms,
                "error": str(e),
                "end_time": datetime.utcnow().isoformat(),
            })
            
            self.record_timer(f"stage.{stage_name}", duration_ms)
            self.increment(f"stage.{stage_name}.failure")
            
            raise
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of pipeline performance"""
        total_duration = sum(
            s.get("duration_ms", 0) 
            for s in self._stage_timings.values()
        )
        
        return {
            "pipeline_id": self.pipeline_id,
            "total_duration_ms": total_duration,
            "stages": self._stage_timings,
            "stats": self.get_all_stats(),
        }


# Global tracker registry
_trackers: Dict[str, PerformanceTracker] = {}


def get_tracker(module: str) -> PerformanceTracker:
    """Get or create a performance tracker for a module"""
    if module not in _trackers:
        _trackers[module] = PerformanceTracker(module)
    return _trackers[module]


def get_pipeline_tracker(pipeline_id: str) -> PipelinePerformanceTracker:
    """Get or create a pipeline performance tracker"""
    key = f"pipeline.{pipeline_id}"
    if key not in _trackers:
        _trackers[key] = PipelinePerformanceTracker(pipeline_id)
    return _trackers[key]


if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    # Test performance tracker
    tracker = get_tracker("test_module")
    
    # Test timing decorator
    @tracker.timed("slow_function")
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    # Run a few times
    for _ in range(5):
        slow_function()
    
    # Test context manager
    with tracker.timer("manual_timing"):
        time.sleep(0.05)
    
    # Test counters and gauges
    tracker.increment("requests")
    tracker.increment("requests")
    tracker.gauge("queue_size", 42)
    
    # Print stats
    print("\nPerformance Statistics:")
    print(json.dumps(tracker.get_all_stats(), indent=2))
    
    # Test pipeline tracker
    print("\n--- Pipeline Tracking ---")
    pipeline_tracker = get_pipeline_tracker("test_pipeline_001")
    
    with pipeline_tracker.track_stage("discovery", {"parcels_found": 10}):
        time.sleep(0.1)
    
    with pipeline_tracker.track_stage("scraping", {"parcels_scraped": 10}):
        time.sleep(0.2)
    
    print("\nPipeline Summary:")
    print(json.dumps(pipeline_tracker.get_pipeline_summary(), indent=2))
