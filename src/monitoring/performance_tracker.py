#!/usr/bin/env python3
"""
Performance Monitoring for SPD Site Plan Development
P2 Codebase Requirement: Performance tracking and metrics

Author: BidDeed.AI / Everest Capital USA
"""

import os
import time
import json
import logging
import threading
import functools
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY = "memory"
    QUEUE_SIZE = "queue_size"


@dataclass
class MetricPoint:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.LATENCY


@dataclass
class PerformanceStats:
    name: str
    count: int
    total: float
    min_val: float
    max_val: float
    avg: float
    p50: float
    p95: float
    p99: float
    stddev: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "avg_ms": round(self.avg, 2),
            "p50_ms": round(self.p50, 2),
            "p95_ms": round(self.p95, 2),
            "p99_ms": round(self.p99, 2),
            "min_ms": round(self.min_val, 2),
            "max_ms": round(self.max_val, 2),
        }


class Timer:
    def __init__(self, name: str, monitor: 'PerformanceMonitor' = None, tags: Dict = None):
        self.name = name
        self.monitor = monitor
        self.tags = tags or {}
        self.duration_ms = None
    
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.perf_counter() - self.start) * 1000
        if self.monitor:
            self.monitor.record_latency(self.name, self.duration_ms, self.tags, exc_type is None)
        return False


class PerformanceMonitor:
    def __init__(self, window_size: int = 1000, flush_interval: int = 60):
        self.window_size = window_size
        self.flush_interval = flush_interval
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._error_counters: Dict[str, int] = {}
        self._baselines: Dict[str, Dict] = {}
        
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
    
    def _get_deque(self, name: str) -> deque:
        if name not in self._metrics:
            with self._lock:
                if name not in self._metrics:
                    self._metrics[name] = deque(maxlen=self.window_size)
        return self._metrics[name]
    
    def record_latency(self, name: str, duration_ms: float, tags: Dict = None, success: bool = True):
        metric = MetricPoint(name=name, value=duration_ms, tags=tags or {})
        self._get_deque(name).append(metric)
        
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + 1
            if not success:
                self._error_counters[name] = self._error_counters.get(name, 0) + 1
        
        self._check_anomaly(name, duration_ms)
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, tags: Dict = None):
        metric = MetricPoint(name=name, value=value, tags=tags or {}, metric_type=metric_type)
        self._get_deque(name).append(metric)
    
    def timer(self, name: str, tags: Dict = None) -> Timer:
        return Timer(name, self, tags)
    
    def timed(self, name: str = None, tags: Dict = None):
        def decorator(func: Callable) -> Callable:
            metric_name = name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.timer(metric_name, tags):
                    return func(*args, **kwargs)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    self.record_latency(metric_name, (time.perf_counter() - start) * 1000, tags, True)
                    return result
                except Exception:
                    self.record_latency(metric_name, (time.perf_counter() - start) * 1000, tags, False)
                    raise
            
            import asyncio
            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
        return decorator
    
    def get_stats(self, name: str, window_minutes: int = 5) -> Optional[PerformanceStats]:
        deq = self._metrics.get(name)
        if not deq:
            return None
        
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        values = [m.value for m in deq if m.timestamp >= cutoff]
        
        if not values:
            return None
        
        sorted_vals = sorted(values)
        n = len(values)
        
        def pct(p): return sorted_vals[min(int(n * p / 100), n - 1)]
        
        return PerformanceStats(
            name=name, count=n, total=sum(values),
            min_val=min(values), max_val=max(values),
            avg=statistics.mean(values),
            p50=pct(50), p95=pct(95), p99=pct(99),
            stddev=statistics.stdev(values) if n > 1 else 0,
        )
    
    def get_all_stats(self) -> Dict[str, Dict]:
        return {name: s.to_dict() for name in self._metrics if (s := self.get_stats(name))}
    
    def get_error_rate(self, name: str) -> float:
        total = self._counters.get(name, 0)
        return self._error_counters.get(name, 0) / total if total else 0.0
    
    def _check_anomaly(self, name: str, value: float):
        baseline = self._baselines.get(name)
        if not baseline:
            stats = self.get_stats(name)
            if stats and stats.count >= 10:
                self._baselines[name] = {"avg": stats.avg, "stddev": stats.stddev}
            return
        
        threshold = baseline["avg"] + 3 * baseline["stddev"]
        if value > threshold:
            logger.warning(f"Anomaly: {name}={value:.2f}ms (threshold={threshold:.2f}ms)")
    
    def _flush_loop(self):
        while self._running:
            time.sleep(self.flush_interval)
            self._flush_metrics()
    
    def _flush_metrics(self):
        if not self.supabase_url or not self.supabase_key:
            return
        try:
            import urllib.request
            for name, stat in self.get_all_stats().items():
                data = {"metric_name": name, **stat, "error_rate": self.get_error_rate(name),
                        "recorded_at": datetime.utcnow().isoformat()}
                req = urllib.request.Request(
                    f"{self.supabase_url}/rest/v1/performance_metrics",
                    data=json.dumps(data).encode(),
                    headers={"Content-Type": "application/json", "apikey": self.supabase_key,
                             "Authorization": f"Bearer {self.supabase_key}"},
                    method="POST")
                urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            logger.debug(f"Flush failed: {e}")
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        stats = self.get_all_stats()
        health_issues = sum(1 for n in stats if self.get_error_rate(n) > 0.05 or stats[n]["p95_ms"] > 5000)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": max(0, 100 - health_issues * 10),
            "metrics": stats,
            "error_rates": {n: self.get_error_rate(n) for n in self._counters},
        }
    
    def shutdown(self):
        self._running = False
        self._flush_metrics()


class PipelineMonitor:
    STAGES = ["discovery", "scraping", "title_search", "lien_priority", "tax_certs",
              "demographics", "ml_score", "max_bid", "decision_log", "report", "disposition", "archive"]
    
    def __init__(self, monitor: PerformanceMonitor = None):
        self.monitor = monitor or PerformanceMonitor()
        self._run_id = None
        self._run_start = None
    
    def start_run(self, run_id: str):
        self._run_id = run_id
        self._run_start = time.perf_counter()
        self.monitor._counters["pipeline_runs"] = self.monitor._counters.get("pipeline_runs", 0) + 1
    
    def end_run(self, success: bool = True):
        if self._run_start:
            self.monitor.record_latency("pipeline_total", (time.perf_counter() - self._run_start) * 1000,
                                        {"run_id": self._run_id}, success)
        self._run_id = self._run_start = None
    
    def stage_timer(self, stage: str) -> Timer:
        return self.monitor.timer(f"stage_{stage}", {"stage": stage, "run_id": self._run_id})
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "stages": {s: self.monitor.get_stats(f"stage_{s}").to_dict() 
                      for s in self.STAGES if self.monitor.get_stats(f"stage_{s}")},
            "total": self.monitor.get_stats("pipeline_total").to_dict() if self.monitor.get_stats("pipeline_total") else None,
        }


_monitor: Optional[PerformanceMonitor] = None

def get_monitor() -> PerformanceMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    @monitor.timed("test_fn")
    def slow_fn():
        time.sleep(0.05)
    
    for _ in range(10):
        slow_fn()
    
    print(json.dumps(monitor.get_dashboard_metrics(), indent=2))
    monitor.shutdown()
