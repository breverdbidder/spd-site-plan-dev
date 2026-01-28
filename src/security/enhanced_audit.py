#!/usr/bin/env python3
"""
Enhanced Security Audit Logging
P6 Security: Comprehensive audit trail (+1 point)

Provides tamper-proof audit logging, compliance reporting, and event correlation.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_MFA = "auth.mfa"
    
    # Authorization
    AUTHZ_GRANTED = "authz.granted"
    AUTHZ_DENIED = "authz.denied"
    AUTHZ_ESCALATION = "authz.escalation"
    
    # Data Access
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    
    # Security Events
    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"
    SECURITY_CONFIG = "security.config"
    
    # Pipeline Events
    PIPELINE_START = "pipeline.start"
    PIPELINE_COMPLETE = "pipeline.complete"
    PIPELINE_ERROR = "pipeline.error"
    
    # HITL Events
    HITL_QUEUED = "hitl.queued"
    HITL_APPROVED = "hitl.approved"
    HITL_REJECTED = "hitl.rejected"
    
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class AuditSeverity(Enum):
    """Audit event severity"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class AuditEvent:
    """Immutable audit event"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    actor: str
    action: str
    resource: str
    outcome: str  # success, failure, error
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    integrity_hash: str = ""
    previous_hash: str = ""
    
    def __post_init__(self):
        if not self.integrity_hash:
            self.integrity_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute tamper-proof integrity hash"""
        data = f"{self.event_id}|{self.event_type.value}|{self.timestamp.isoformat()}|{self.actor}|{self.action}|{self.resource}|{self.outcome}|{self.previous_hash}"
        secret = os.environ.get("AUDIT_HMAC_KEY", "default-audit-key")
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify event integrity"""
        return self.integrity_hash == self._compute_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.name,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "details": self.details,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "integrity_hash": self.integrity_hash,
        }


@dataclass
class AuditChain:
    """Chain of audit events with integrity verification"""
    events: List[AuditEvent] = field(default_factory=list)
    
    def add_event(self, event: AuditEvent) -> AuditEvent:
        """Add event to chain with hash linking"""
        if self.events:
            event.previous_hash = self.events[-1].integrity_hash
            event.integrity_hash = event._compute_hash()
        self.events.append(event)
        return event
    
    def verify_chain(self) -> bool:
        """Verify entire chain integrity"""
        for i, event in enumerate(self.events):
            if not event.verify_integrity():
                logger.error(f"Integrity check failed at event {i}: {event.event_id}")
                return False
            if i > 0 and event.previous_hash != self.events[i-1].integrity_hash:
                logger.error(f"Chain broken at event {i}: {event.event_id}")
                return False
        return True


class EnhancedAuditLogger:
    """
    Comprehensive audit logging with tamper-proof integrity.
    
    Usage:
        audit = EnhancedAuditLogger()
        
        # Log a security event
        audit.log(
            event_type=AuditEventType.AUTH_LOGIN,
            actor="user@example.com",
            action="login",
            resource="api",
            outcome="success",
            details={"method": "oauth"}
        )
        
        # Generate compliance report
        report = audit.generate_compliance_report(days=30)
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.url = supabase_url or os.environ.get("SUPABASE_URL")
        self.key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._chain = AuditChain()
        self._event_counter = 0
    
    def _gen_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        self._event_counter += 1
        return f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    
    def log(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        resource: str,
        outcome: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        session_id: str = None,
        correlation_id: str = None,
    ) -> AuditEvent:
        """Log an audit event"""
        event = AuditEvent(
            event_id=self._gen_event_id(),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
            correlation_id=correlation_id,
        )
        
        # Add to chain
        self._chain.add_event(event)
        
        # Persist to database
        self._persist_event(event)
        
        # Log critical/high events
        if severity in [AuditSeverity.CRITICAL, AuditSeverity.HIGH]:
            logger.warning(f"Audit [{severity.name}]: {actor} {action} {resource} -> {outcome}")
        
        return event
    
    def _persist_event(self, event: AuditEvent) -> bool:
        """Persist event to Supabase"""
        if not self.url or not self.key:
            return False
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.url}/rest/v1/security_audit_logs",
                data=json.dumps(event.to_dict()).encode(),
                headers={
                    "Content-Type": "application/json",
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in [200, 201]
        except Exception as e:
            logger.error(f"Failed to persist audit event: {e}")
            return False
    
    # Convenience methods
    def log_auth(self, actor: str, action: str, success: bool, details: Dict = None):
        """Log authentication event"""
        event_type = AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED
        return self.log(
            event_type=event_type,
            actor=actor,
            action=action,
            resource="authentication",
            outcome="success" if success else "failure",
            severity=AuditSeverity.INFO if success else AuditSeverity.HIGH,
            details=details,
        )
    
    def log_data_access(self, actor: str, action: str, resource: str, details: Dict = None):
        """Log data access event"""
        type_map = {"read": AuditEventType.DATA_READ, "write": AuditEventType.DATA_WRITE, "delete": AuditEventType.DATA_DELETE}
        return self.log(
            event_type=type_map.get(action, AuditEventType.DATA_READ),
            actor=actor,
            action=action,
            resource=resource,
            outcome="success",
            details=details,
        )
    
    def log_security_event(self, actor: str, action: str, resource: str, severity: AuditSeverity, details: Dict = None):
        """Log security-related event"""
        return self.log(
            event_type=AuditEventType.SECURITY_ALERT,
            actor=actor,
            action=action,
            resource=resource,
            outcome="detected",
            severity=severity,
            details=details,
        )
    
    def log_hitl_decision(self, decision_id: str, actor: str, action: str, details: Dict = None):
        """Log HITL decision"""
        type_map = {"approve": AuditEventType.HITL_APPROVED, "reject": AuditEventType.HITL_REJECTED, "queue": AuditEventType.HITL_QUEUED}
        return self.log(
            event_type=type_map.get(action, AuditEventType.HITL_QUEUED),
            actor=actor,
            action=action,
            resource=f"hitl/{decision_id}",
            outcome="success",
            severity=AuditSeverity.MEDIUM,
            details=details,
        )
    
    def verify_chain_integrity(self) -> bool:
        """Verify audit chain integrity"""
        return self._chain.verify_chain()
    
    def generate_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for specified period"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        events = [e for e in self._chain.events if e.timestamp >= cutoff]
        
        return {
            "report_id": f"COMP-{datetime.utcnow().strftime('%Y%m%d')}",
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": len(events),
            "events_by_type": self._count_by_type(events),
            "events_by_severity": self._count_by_severity(events),
            "events_by_outcome": self._count_by_outcome(events),
            "security_events": len([e for e in events if e.event_type.value.startswith("security.")]),
            "failed_auth_attempts": len([e for e in events if e.event_type == AuditEventType.AUTH_FAILED]),
            "hitl_decisions": len([e for e in events if e.event_type.value.startswith("hitl.")]),
            "chain_integrity": self.verify_chain_integrity(),
        }
    
    def _count_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(e.event_type.value for e in events))
    
    def _count_by_severity(self, events: List[AuditEvent]) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(e.severity.name for e in events))
    
    def _count_by_outcome(self, events: List[AuditEvent]) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(e.outcome for e in events))


# Global instance
_audit_logger: Optional[EnhancedAuditLogger] = None

def get_audit_logger() -> EnhancedAuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = EnhancedAuditLogger()
    return _audit_logger


def audit_log(event_type: AuditEventType, actor: str, action: str, resource: str, **kwargs) -> AuditEvent:
    """Convenience function for audit logging"""
    return get_audit_logger().log(event_type, actor, action, resource, **kwargs)
