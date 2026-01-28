#!/usr/bin/env python3
"""
Real-time Security Alerting System
P5 Security: Enhanced monitoring (+3 points)

Provides immediate notification via Slack/email when security threats are detected.
Integrates with threat detection and anomaly monitoring systems.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SUPABASE = "supabase"
    CONSOLE = "console"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    threat_type: str
    source: str
    timestamp: str
    metadata: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False


class SecurityAlertManager:
    """
    Real-time security alerting manager.
    
    Features:
    - Multi-channel alerting (Slack, email, webhooks)
    - Severity-based routing
    - Alert deduplication
    - Escalation policies
    - Audit trail in Supabase
    
    Usage:
        manager = SecurityAlertManager(
            slack_webhook=os.environ.get("SLACK_SECURITY_WEBHOOK")
        )
        
        # Send critical alert
        manager.send_alert(
            severity=AlertSeverity.CRITICAL,
            title="SQL Injection Detected",
            description="UNION SELECT attack blocked",
            threat_type="SQL_INJECTION",
            source="api_gateway"
        )
    """
    
    def __init__(
        self,
        slack_webhook: str = None,
        email_endpoint: str = None,
        supabase_url: str = None,
        supabase_key: str = None
    ):
        self.slack_webhook = slack_webhook or os.environ.get("SLACK_SECURITY_WEBHOOK")
        self.email_endpoint = email_endpoint or os.environ.get("EMAIL_ALERT_ENDPOINT")
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        # Alert tracking
        self._recent_alerts: Dict[str, datetime] = {}
        self._alert_count = 0
        
        # Deduplication window (seconds)
        self.dedup_window = 300  # 5 minutes
        
        # Severity routing
        self.severity_channels = {
            AlertSeverity.INFO: [AlertChannel.CONSOLE, AlertChannel.SUPABASE],
            AlertSeverity.WARNING: [AlertChannel.CONSOLE, AlertChannel.SUPABASE, AlertChannel.SLACK],
            AlertSeverity.HIGH: [AlertChannel.CONSOLE, AlertChannel.SUPABASE, AlertChannel.SLACK],
            AlertSeverity.CRITICAL: [AlertChannel.CONSOLE, AlertChannel.SUPABASE, AlertChannel.SLACK, AlertChannel.EMAIL],
        }
    
    def _generate_alert_id(self, title: str, threat_type: str) -> str:
        """Generate unique alert ID"""
        import hashlib
        content = f"{title}:{threat_type}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _is_duplicate(self, alert_id: str) -> bool:
        """Check if alert is duplicate within dedup window"""
        if alert_id in self._recent_alerts:
            last_sent = self._recent_alerts[alert_id]
            if (datetime.utcnow() - last_sent).total_seconds() < self.dedup_window:
                return True
        return False
    
    def send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        description: str,
        threat_type: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> SecurityAlert:
        """
        Send security alert through configured channels.
        
        Args:
            severity: Alert severity level
            title: Alert title
            description: Detailed description
            threat_type: Type of threat detected
            source: Source system/component
            metadata: Additional context
            
        Returns:
            SecurityAlert object
        """
        alert_id = self._generate_alert_id(title, threat_type)
        
        # Check for duplicates
        if self._is_duplicate(alert_id):
            logger.debug(f"Duplicate alert suppressed: {alert_id}")
            return None
        
        alert = SecurityAlert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            threat_type=threat_type,
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        # Route to appropriate channels
        channels = self.severity_channels.get(severity, [AlertChannel.CONSOLE])
        
        for channel in channels:
            try:
                if channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.SUPABASE:
                    self._log_to_supabase(alert)
                elif channel == AlertChannel.CONSOLE:
                    self._log_to_console(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
        
        # Track alert
        self._recent_alerts[alert_id] = datetime.utcnow()
        self._alert_count += 1
        
        return alert
    
    def _send_slack_alert(self, alert: SecurityAlert):
        """Send alert to Slack"""
        if not self.slack_webhook:
            logger.debug("Slack webhook not configured")
            return
        
        # Severity emoji
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.HIGH: "🔴",
            AlertSeverity.CRITICAL: "🚨",
        }
        
        # Severity color
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.HIGH: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000",
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#808080"),
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji_map.get(alert.severity, '🔔')} {alert.title}",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity.value.upper()}"},
                                {"type": "mrkdwn", "text": f"*Threat Type:*\n{alert.threat_type}"},
                                {"type": "mrkdwn", "text": f"*Source:*\n{alert.source}"},
                                {"type": "mrkdwn", "text": f"*Time:*\n{alert.timestamp}"},
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Description:*\n{alert.description}"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {"type": "mrkdwn", "text": f"Alert ID: `{alert.alert_id}` | SPD.AI Security Monitor"}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Add metadata if present
        if alert.metadata:
            metadata_text = "\n".join([f"• {k}: {v}" for k, v in alert.metadata.items()])
            payload["attachments"][0]["blocks"].insert(3, {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Additional Context:*\n{metadata_text}"}
            })
        
        try:
            req = urllib.request.Request(
                self.slack_webhook,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.info(f"Slack alert sent: {alert.alert_id}")
        except urllib.error.URLError as e:
            logger.error(f"Slack alert failed: {e}")
    
    def _send_email_alert(self, alert: SecurityAlert):
        """Send alert via email (requires email service endpoint)"""
        if not self.email_endpoint:
            logger.debug("Email endpoint not configured")
            return
        
        payload = {
            "to": os.environ.get("SECURITY_EMAIL", "security@biddeed.ai"),
            "subject": f"[{alert.severity.value.upper()}] {alert.title}",
            "body": f"""
Security Alert - SPD.AI

Alert ID: {alert.alert_id}
Severity: {alert.severity.value.upper()}
Threat Type: {alert.threat_type}
Source: {alert.source}
Time: {alert.timestamp}

Description:
{alert.description}

Metadata:
{json.dumps(alert.metadata, indent=2)}

---
This is an automated security alert from SPD.AI Security Monitor.
            """.strip()
        }
        
        try:
            req = urllib.request.Request(
                self.email_endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"Email alert sent: {alert.alert_id}")
        except urllib.error.URLError as e:
            logger.error(f"Email alert failed: {e}")
    
    def _log_to_supabase(self, alert: SecurityAlert):
        """Log alert to Supabase for audit trail"""
        if not self.supabase_url or not self.supabase_key:
            logger.debug("Supabase not configured")
            return
        
        payload = {
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "threat_type": alert.threat_type,
            "source": alert.source,
            "metadata": alert.metadata,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "created_at": alert.timestamp,
        }
        
        try:
            url = f"{self.supabase_url}/rest/v1/security_alerts"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Prefer": "return=minimal"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"Alert logged to Supabase: {alert.alert_id}")
        except urllib.error.URLError as e:
            logger.error(f"Supabase logging failed: {e}")
    
    def _log_to_console(self, alert: SecurityAlert):
        """Log alert to console"""
        severity_colors = {
            AlertSeverity.INFO: "\033[94m",     # Blue
            AlertSeverity.WARNING: "\033[93m",  # Yellow
            AlertSeverity.HIGH: "\033[91m",     # Red
            AlertSeverity.CRITICAL: "\033[95m", # Magenta
        }
        reset = "\033[0m"
        color = severity_colors.get(alert.severity, "")
        
        print(f"""
{color}{'='*60}
SECURITY ALERT [{alert.severity.value.upper()}]
{'='*60}{reset}
ID:          {alert.alert_id}
Title:       {alert.title}
Threat:      {alert.threat_type}
Source:      {alert.source}
Time:        {alert.timestamp}
Description: {alert.description}
{color}{'='*60}{reset}
""")
    
    def send_critical_alert(self, threat_type: str, details: Dict[str, Any]):
        """Convenience method for critical alerts"""
        return self.send_alert(
            severity=AlertSeverity.CRITICAL,
            title=f"Critical Security Threat: {threat_type}",
            description=details.get("description", "Critical security event detected"),
            threat_type=threat_type,
            source=details.get("source", "unknown"),
            metadata=details
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alerting statistics"""
        return {
            "total_alerts": self._alert_count,
            "active_dedup_keys": len(self._recent_alerts),
            "channels_configured": {
                "slack": bool(self.slack_webhook),
                "email": bool(self.email_endpoint),
                "supabase": bool(self.supabase_url and self.supabase_key),
            }
        }


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_alert_manager: Optional[SecurityAlertManager] = None


def get_alert_manager() -> SecurityAlertManager:
    """Get singleton alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = SecurityAlertManager()
    return _alert_manager


def send_security_alert(
    severity: AlertSeverity,
    title: str,
    description: str,
    threat_type: str,
    source: str = "system"
) -> SecurityAlert:
    """Quick helper to send security alert"""
    return get_alert_manager().send_alert(
        severity=severity,
        title=title,
        description=description,
        threat_type=threat_type,
        source=source
    )


if __name__ == "__main__":
    # Demo alerting
    manager = SecurityAlertManager()
    
    print("=== Security Alert Manager Demo ===\n")
    
    # Test alerts at different severities
    manager.send_alert(
        severity=AlertSeverity.INFO,
        title="System Health Check",
        description="All security systems operational",
        threat_type="HEALTH_CHECK",
        source="monitoring"
    )
    
    manager.send_alert(
        severity=AlertSeverity.WARNING,
        title="Unusual Login Pattern",
        description="Multiple failed login attempts from IP 192.168.1.100",
        threat_type="BRUTE_FORCE",
        source="auth_service",
        metadata={"ip": "192.168.1.100", "attempts": 5}
    )
    
    manager.send_alert(
        severity=AlertSeverity.CRITICAL,
        title="SQL Injection Blocked",
        description="UNION SELECT attack detected and blocked",
        threat_type="SQL_INJECTION",
        source="api_gateway",
        metadata={"endpoint": "/api/properties", "blocked": True}
    )
    
    print(f"\nStats: {manager.get_stats()}")
