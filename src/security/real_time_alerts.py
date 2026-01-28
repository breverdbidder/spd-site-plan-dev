#!/usr/bin/env python3
"""
Real-Time Security Alerts System
P5 Security: Real-time alerts + anomaly detection (+3 points)

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AlertChannel(Enum):
    SLACK = "slack"
    EMAIL = "email"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class SecurityAlert:
    alert_id: str
    severity: AlertSeverity
    category: str
    title: str
    description: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class AlertDeduplicator:
    def __init__(self, window_minutes: int = 15):
        self.window = timedelta(minutes=window_minutes)
        self._seen: Dict[str, datetime] = {}
        self._counts: Dict[str, int] = defaultdict(int)
    
    def _hash(self, alert: SecurityAlert) -> str:
        key = f"{alert.category}:{alert.title}:{alert.source}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def should_send(self, alert: SecurityAlert) -> bool:
        h = self._hash(alert)
        now = datetime.utcnow()
        self._seen = {k: v for k, v in self._seen.items() if now - v < self.window}
        if h in self._seen:
            self._counts[h] += 1
            return False
        self._seen[h] = now
        return True


class SlackAlerter:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_SECURITY_WEBHOOK")
    
    async def send(self, alert: SecurityAlert) -> bool:
        if not self.webhook_url:
            return False
        emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📢", "LOW": "ℹ️"}.get(alert.severity.value, "📝")
        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {alert.severity.value}: {alert.title}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Category:* {alert.category}\n*Source:* {alert.source}\n*Description:* {alert.description}"}}
            ]
        }
        try:
            import urllib.request
            req = urllib.request.Request(self.webhook_url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except:
            return False


class DashboardAlerter:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    async def send(self, alert: SecurityAlert) -> bool:
        if not self.url or not self.key:
            return False
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.url}/rest/v1/security_alerts",
                data=json.dumps(alert.to_dict()).encode(),
                headers={"Content-Type": "application/json", "apikey": self.key, "Authorization": f"Bearer {self.key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in [200, 201]
        except:
            return False


class RealTimeAlertManager:
    def __init__(self):
        self.slack = SlackAlerter()
        self.dashboard = DashboardAlerter()
        self.dedup = AlertDeduplicator()
    
    def _gen_id(self) -> str:
        import uuid
        return f"ALT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    async def alert(self, severity: AlertSeverity, category: str, title: str, description: str, source: str, metadata: Dict = None) -> SecurityAlert:
        alert = SecurityAlert(self._gen_id(), severity, category, title, description, source, metadata=metadata or {})
        if not self.dedup.should_send(alert):
            return alert
        tasks = [self.dashboard.send(alert)]
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            tasks.append(self.slack.send(alert))
        await asyncio.gather(*tasks, return_exceptions=True)
        return alert
    
    async def injection_detected(self, source: str, pattern: str):
        return await self.alert(AlertSeverity.HIGH, "PROMPT_INJECTION", "Injection Detected", f"Pattern: {pattern[:100]}", source)
    
    async def exfiltration_detected(self, source: str, data_type: str):
        return await self.alert(AlertSeverity.CRITICAL, "DATA_EXFILTRATION", "Exfiltration Attempt", f"Type: {data_type}", source)
    
    async def privilege_escalation(self, source: str, from_role: str, to_role: str):
        return await self.alert(AlertSeverity.CRITICAL, "PRIVILEGE_ESCALATION", "Privilege Escalation", f"{from_role} -> {to_role}", source)
    
    async def anomaly(self, source: str, anomaly_type: str, details: str):
        return await self.alert(AlertSeverity.HIGH, "ANOMALY", f"Anomaly: {anomaly_type}", details, source)


_manager: Optional[RealTimeAlertManager] = None

def get_alert_manager() -> RealTimeAlertManager:
    global _manager
    if _manager is None:
        _manager = RealTimeAlertManager()
    return _manager
