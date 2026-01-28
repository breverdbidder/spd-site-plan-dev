#!/usr/bin/env python3
"""
Human-in-the-Loop (HITL) Dashboard System
P5 Security: HITL system completion (+3 points)

Manages high-value decisions, approval workflows, and manual overrides.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HITLStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    EXPIRED = "EXPIRED"
    AUTO_APPROVED = "AUTO_APPROVED"


class HITLTriggerType(Enum):
    HIGH_VALUE = "HIGH_VALUE"           # >$500K property value
    LOW_CONFIDENCE = "LOW_CONFIDENCE"   # <40% ML confidence
    COMPLEX_LIENS = "COMPLEX_LIENS"     # >5 liens detected
    ANOMALY = "ANOMALY"                 # Security anomaly
    MANUAL_FLAG = "MANUAL_FLAG"         # Manually flagged
    FIRST_TIME = "FIRST_TIME"           # First transaction type


@dataclass
class HITLDecision:
    decision_id: str
    trigger_type: HITLTriggerType
    status: HITLStatus
    title: str
    description: str
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_notes: Optional[str] = None
    auto_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "trigger_type": self.trigger_type.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
            "decision_notes": self.decision_notes,
        }


@dataclass
class HITLThresholds:
    high_value_amount: float = 500000.0
    low_confidence_pct: float = 40.0
    complex_liens_count: int = 5
    decision_timeout_hours: int = 24
    auto_approve_below: float = 100000.0


class HITLQueue:
    """Manages the queue of decisions requiring human review"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.url = supabase_url or os.environ.get("SUPABASE_URL")
        self.key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._local_queue: List[HITLDecision] = []
        self.thresholds = HITLThresholds()
    
    def _gen_id(self) -> str:
        import uuid
        return f"HITL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    async def add_decision(self, trigger_type: HITLTriggerType, title: str, description: str, context: Dict[str, Any], timeout_hours: int = None) -> HITLDecision:
        """Add a new decision to the HITL queue"""
        timeout = timeout_hours or self.thresholds.decision_timeout_hours
        decision = HITLDecision(
            decision_id=self._gen_id(),
            trigger_type=trigger_type,
            status=HITLStatus.PENDING,
            title=title,
            description=description,
            context=context,
            expires_at=datetime.utcnow() + timedelta(hours=timeout),
        )
        
        # Store in Supabase
        await self._store_decision(decision)
        self._local_queue.append(decision)
        
        logger.info(f"HITL decision queued: {decision.decision_id}")
        return decision
    
    async def _store_decision(self, decision: HITLDecision) -> bool:
        """Store decision in Supabase"""
        if not self.url or not self.key:
            return False
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.url}/rest/v1/hitl_decisions",
                data=json.dumps(decision.to_dict()).encode(),
                headers={"Content-Type": "application/json", "apikey": self.key, "Authorization": f"Bearer {self.key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in [200, 201]
        except Exception as e:
            logger.error(f"Failed to store HITL decision: {e}")
            return False
    
    async def approve(self, decision_id: str, approved_by: str, notes: str = None) -> bool:
        """Approve a pending decision"""
        return await self._update_status(decision_id, HITLStatus.APPROVED, approved_by, notes)
    
    async def reject(self, decision_id: str, rejected_by: str, notes: str = None) -> bool:
        """Reject a pending decision"""
        return await self._update_status(decision_id, HITLStatus.REJECTED, rejected_by, notes)
    
    async def escalate(self, decision_id: str, escalated_by: str, notes: str = None) -> bool:
        """Escalate a decision to higher authority"""
        return await self._update_status(decision_id, HITLStatus.ESCALATED, escalated_by, notes)
    
    async def _update_status(self, decision_id: str, status: HITLStatus, by: str, notes: str = None) -> bool:
        """Update decision status"""
        if not self.url or not self.key:
            return False
        try:
            import urllib.request
            data = {
                "status": status.value,
                "decided_at": datetime.utcnow().isoformat(),
                "decided_by": by,
                "decision_notes": notes,
            }
            req = urllib.request.Request(
                f"{self.url}/rest/v1/hitl_decisions?decision_id=eq.{decision_id}",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json", "apikey": self.key, "Authorization": f"Bearer {self.key}"},
                method="PATCH"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in [200, 204]
        except Exception as e:
            logger.error(f"Failed to update HITL decision: {e}")
            return False
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get all pending decisions"""
        if not self.url or not self.key:
            return [d.to_dict() for d in self._local_queue if d.status == HITLStatus.PENDING]
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.url}/rest/v1/hitl_decisions?status=eq.PENDING&order=created_at.asc",
                headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except:
            return []
    
    async def check_expired(self) -> int:
        """Check and mark expired decisions"""
        if not self.url or not self.key:
            return 0
        try:
            import urllib.request
            now = datetime.utcnow().isoformat()
            data = {"status": HITLStatus.EXPIRED.value}
            req = urllib.request.Request(
                f"{self.url}/rest/v1/hitl_decisions?status=eq.PENDING&expires_at=lt.{now}",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json", "apikey": self.key, "Authorization": f"Bearer {self.key}", "Prefer": "return=representation"},
                method="PATCH"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return len(result) if isinstance(result, list) else 0
        except:
            return 0


class HITLTriggerEvaluator:
    """Evaluates if a transaction requires HITL review"""
    
    def __init__(self, thresholds: HITLThresholds = None):
        self.thresholds = thresholds or HITLThresholds()
    
    def evaluate(self, context: Dict[str, Any]) -> Optional[HITLTriggerType]:
        """Evaluate if context requires HITL review"""
        # High value check
        value = context.get("property_value", 0) or context.get("bid_amount", 0)
        if value >= self.thresholds.high_value_amount:
            return HITLTriggerType.HIGH_VALUE
        
        # Low confidence check
        confidence = context.get("ml_confidence", 100) or context.get("score", 100)
        if confidence < self.thresholds.low_confidence_pct:
            return HITLTriggerType.LOW_CONFIDENCE
        
        # Complex liens check
        lien_count = context.get("lien_count", 0) or len(context.get("liens", []))
        if lien_count > self.thresholds.complex_liens_count:
            return HITLTriggerType.COMPLEX_LIENS
        
        # Anomaly flag
        if context.get("anomaly_detected") or context.get("is_anomaly"):
            return HITLTriggerType.ANOMALY
        
        # Manual flag
        if context.get("manual_review") or context.get("flagged"):
            return HITLTriggerType.MANUAL_FLAG
        
        return None
    
    def should_auto_approve(self, context: Dict[str, Any]) -> bool:
        """Check if transaction can be auto-approved"""
        value = context.get("property_value", 0) or context.get("bid_amount", 0)
        confidence = context.get("ml_confidence", 0) or context.get("score", 0)
        
        return (
            value < self.thresholds.auto_approve_below
            and confidence >= 70
            and not context.get("anomaly_detected")
            and not context.get("manual_review")
        )


class HITLDashboard:
    """
    Main HITL Dashboard interface.
    
    Usage:
        dashboard = HITLDashboard()
        
        # Check if review needed
        trigger = dashboard.check_review_needed({"property_value": 600000, "score": 85})
        
        # Queue for review if needed
        if trigger:
            await dashboard.queue_for_review(trigger, "High value property", context)
        
        # Approve/reject
        await dashboard.approve("HITL-20260128-ABC12345", "ariel@biddeed.ai", "Approved after verification")
    """
    
    def __init__(self):
        self.queue = HITLQueue()
        self.evaluator = HITLTriggerEvaluator(self.queue.thresholds)
    
    def check_review_needed(self, context: Dict[str, Any]) -> Optional[HITLTriggerType]:
        """Check if context requires HITL review"""
        return self.evaluator.evaluate(context)
    
    def can_auto_approve(self, context: Dict[str, Any]) -> bool:
        """Check if can be auto-approved"""
        return self.evaluator.should_auto_approve(context)
    
    async def queue_for_review(self, trigger_type: HITLTriggerType, title: str, context: Dict[str, Any], description: str = None) -> HITLDecision:
        """Queue a decision for human review"""
        desc = description or f"Triggered by: {trigger_type.value}"
        return await self.queue.add_decision(trigger_type, title, desc, context)
    
    async def approve(self, decision_id: str, approved_by: str, notes: str = None) -> bool:
        """Approve a decision"""
        return await self.queue.approve(decision_id, approved_by, notes)
    
    async def reject(self, decision_id: str, rejected_by: str, notes: str = None) -> bool:
        """Reject a decision"""
        return await self.queue.reject(decision_id, rejected_by, notes)
    
    async def get_pending_count(self) -> int:
        """Get count of pending decisions"""
        pending = await self.queue.get_pending()
        return len(pending)
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        pending = await self.queue.get_pending()
        return {
            "pending_count": len(pending),
            "oldest_pending": pending[0]["created_at"] if pending else None,
            "by_trigger_type": self._count_by_type(pending),
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _count_by_type(self, decisions: List[Dict]) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(d.get("trigger_type") for d in decisions))


# Global instance
_dashboard: Optional[HITLDashboard] = None

def get_hitl_dashboard() -> HITLDashboard:
    global _dashboard
    if _dashboard is None:
        _dashboard = HITLDashboard()
    return _dashboard
