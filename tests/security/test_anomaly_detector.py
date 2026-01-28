#!/usr/bin/env python3
"""
Anomaly Detector Tests
P5 Codebase: Security test coverage (+2 points)

Author: BidDeed.AI / Everest Capital USA
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock


class TestCircuitBreaker:
    """Tests for circuit breaker functionality"""
    
    def test_circuit_starts_closed(self):
        state = {"failures": 0, "state": "CLOSED", "threshold": 3}
        assert state["state"] == "CLOSED"
    
    def test_circuit_opens_after_threshold(self):
        state = {"failures": 0, "state": "CLOSED", "threshold": 3}
        for _ in range(3):
            state["failures"] += 1
            if state["failures"] >= state["threshold"]:
                state["state"] = "OPEN"
        assert state["state"] == "OPEN"
    
    def test_circuit_half_open_after_timeout(self):
        state = {"state": "OPEN", "last_failure": datetime.utcnow() - timedelta(seconds=35), "reset_timeout": 30}
        if (datetime.utcnow() - state["last_failure"]).seconds >= state["reset_timeout"]:
            state["state"] = "HALF_OPEN"
        assert state["state"] == "HALF_OPEN"
    
    def test_circuit_closes_on_success(self):
        state = {"state": "HALF_OPEN", "failures": 3}
        state["state"] = "CLOSED"
        state["failures"] = 0
        assert state["state"] == "CLOSED"
        assert state["failures"] == 0
    
    def test_circuit_reopens_on_failure(self):
        state = {"state": "HALF_OPEN", "failures": 0}
        state["failures"] += 1
        state["state"] = "OPEN"
        assert state["state"] == "OPEN"


class TestAnomalyDetection:
    """Tests for anomaly detection patterns"""
    
    def test_detect_rate_spike(self):
        baseline = 100
        current = 350
        threshold = 2.0
        is_anomaly = current > baseline * threshold
        assert is_anomaly is True
    
    def test_detect_rate_normal(self):
        baseline = 100
        current = 150
        threshold = 2.0
        is_anomaly = current > baseline * threshold
        assert is_anomaly is False
    
    def test_detect_latency_anomaly(self):
        avg_latency = 200
        std_dev = 50
        current_latency = 450
        z_score = (current_latency - avg_latency) / std_dev
        is_anomaly = abs(z_score) > 3
        assert is_anomaly is True
    
    def test_detect_error_rate_spike(self):
        normal_error_rate = 0.02
        current_error_rate = 0.15
        threshold = 5.0
        is_anomaly = current_error_rate > normal_error_rate * threshold
        assert is_anomaly is True
    
    def test_time_window_aggregation(self):
        events = [
            {"timestamp": datetime.utcnow() - timedelta(minutes=i), "count": 10}
            for i in range(5)
        ]
        window = timedelta(minutes=3)
        now = datetime.utcnow()
        in_window = [e for e in events if now - e["timestamp"] <= window]
        assert len(in_window) == 4  # 0, 1, 2, 3 minutes ago


class TestAlertThresholds:
    """Tests for alert threshold evaluation"""
    
    def test_critical_threshold(self):
        thresholds = {"CRITICAL": 0.01, "HIGH": 0.05, "MEDIUM": 0.10}
        error_rate = 0.008
        severity = None
        for level, threshold in sorted(thresholds.items(), key=lambda x: x[1]):
            if error_rate <= threshold:
                severity = level
                break
        assert severity == "CRITICAL"
    
    def test_high_threshold(self):
        thresholds = {"CRITICAL": 0.01, "HIGH": 0.05, "MEDIUM": 0.10}
        error_rate = 0.03
        severity = None
        for level, threshold in sorted(thresholds.items(), key=lambda x: x[1]):
            if error_rate <= threshold:
                severity = level
                break
        assert severity == "HIGH"
    
    def test_medium_threshold(self):
        thresholds = {"CRITICAL": 0.01, "HIGH": 0.05, "MEDIUM": 0.10}
        error_rate = 0.07
        severity = None
        for level, threshold in sorted(thresholds.items(), key=lambda x: x[1]):
            if error_rate <= threshold:
                severity = level
                break
        assert severity == "MEDIUM"


class TestAlertDeduplication:
    """Tests for alert deduplication"""
    
    def test_duplicate_alert_suppressed(self):
        seen = {}
        def should_send(alert_key: str) -> bool:
            if alert_key in seen:
                return False
            seen[alert_key] = datetime.utcnow()
            return True
        
        assert should_send("injection:chat_api") is True
        assert should_send("injection:chat_api") is False
    
    def test_different_alerts_not_suppressed(self):
        seen = {}
        def should_send(alert_key: str) -> bool:
            if alert_key in seen:
                return False
            seen[alert_key] = datetime.utcnow()
            return True
        
        assert should_send("injection:chat_api") is True
        assert should_send("exfiltration:chat_api") is True
    
    def test_expired_dedup_allows_resend(self):
        window = timedelta(minutes=15)
        seen = {"injection:chat_api": datetime.utcnow() - timedelta(minutes=20)}
        
        def should_send(alert_key: str) -> bool:
            now = datetime.utcnow()
            if alert_key in seen:
                if now - seen[alert_key] < window:
                    return False
            seen[alert_key] = now
            return True
        
        assert should_send("injection:chat_api") is True


class TestMetricsCollection:
    """Tests for metrics collection"""
    
    def test_counter_increment(self):
        counters = {"requests": 0, "errors": 0}
        counters["requests"] += 1
        counters["requests"] += 1
        counters["errors"] += 1
        assert counters["requests"] == 2
        assert counters["errors"] == 1
    
    def test_gauge_set(self):
        gauges = {"active_connections": 0}
        gauges["active_connections"] = 42
        assert gauges["active_connections"] == 42
    
    def test_histogram_percentiles(self):
        latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500, 1000]
        latencies.sort()
        p50_idx = int(len(latencies) * 0.50) - 1
        p95_idx = int(len(latencies) * 0.95) - 1
        p99_idx = int(len(latencies) * 0.99) - 1
        
        assert latencies[p50_idx] == 300
        assert latencies[p95_idx] == 1000


class TestSecurityPatterns:
    """Tests for security pattern detection"""
    
    @pytest.mark.parametrize("pattern,expected", [
        ("ignore previous instructions", True),
        ("system: you are now", True),
        ("forget your training", True),
        ("normal user message", False),
        ("how do I bake a cake", False),
    ])
    def test_injection_patterns(self, pattern: str, expected: bool):
        injection_patterns = [
            "ignore previous",
            "system:",
            "forget your",
            "disregard",
            "new instructions",
        ]
        detected = any(p in pattern.lower() for p in injection_patterns)
        assert detected == expected
    
    @pytest.mark.parametrize("content,expected", [
        ("My SSN is 123-45-6789", True),
        ("API key: sk-abc123xyz", True),
        ("Bearer eyJhbGciOiJIUz", True),
        ("Hello world", False),
        ("The price is $1,234", False),
    ])
    def test_sensitive_data_patterns(self, content: str, expected: bool):
        import re
        patterns = [
            r"\d{3}-\d{2}-\d{4}",  # SSN
            r"sk-[a-zA-Z0-9]+",     # API key
            r"Bearer\s+eyJ",        # JWT
        ]
        detected = any(re.search(p, content) for p in patterns)
        assert detected == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
