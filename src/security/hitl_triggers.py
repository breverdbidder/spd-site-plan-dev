#!/usr/bin/env python3
"""
Human-in-the-Loop (HITL) Triggers for SPD Site Plan Development
P5 Security: High-risk decision triggers (+3 points per Greptile)

Implements:
- High-value property thresholds (>$500K)
- Low confidence ML score flags (<40%)
- Complex scenario detection (>5 liens)
- Daily review queue for Ariel (20 min max)

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of HITL triggers"""
    HIGH_VALUE = "HIGH_VALUE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    COMPLEX_LIENS = "COMPLEX_LIENS"
    ANOMALY = "ANOMALY"
    SECURITY = "SECURITY"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class TriggerPriority(Enum):
    """Priority levels for review queue"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TriggerStatus(Enum):
    """Status of triggered items"""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class HITLTrigger:
    """A triggered item requiring human review"""
    id: str
    trigger_type: TriggerType
    priority: TriggerPriority
    status: TriggerStatus
    title: str
    description: str
    data: Dict[str, Any]
    triggered_at: datetime
    triggered_by: str  # Agent name
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    decision: Optional[str] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "triggered_at": self.triggered_at.isoformat(),
            "triggered_by": self.triggered_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "decision": self.decision,
            "notes": self.notes,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


# =============================================================================
# TRIGGER THRESHOLDS CONFIGURATION
# =============================================================================

HITL_THRESHOLDS = {
    # High-value property threshold
    "high_value_usd": 500_000,
    
    # Low confidence ML score
    "low_confidence_score": 40,
    
    # Complex liens threshold
    "complex_liens_count": 5,
    
    # Anomaly detection threshold
    "anomaly_score": 0.8,
    
    # Review queue limits (Ariel's 20 min daily)
    "max_daily_reviews": 10,
    "review_time_minutes": 2,  # Average time per review
    
    # Expiration (auto-approve after X hours if not reviewed)
    "low_priority_expiry_hours": 48,
    "high_priority_expiry_hours": 24,
    "critical_expiry_hours": 12,
}


class HITLTriggerManager:
    """
    Manages human-in-the-loop triggers and review queue.
    
    Usage:
        manager = HITLTriggerManager()
        
        # Check if property needs review
        if manager.should_trigger_review(property_data, ml_score):
            trigger = manager.create_trigger(...)
            
        # Get Ariel's daily review queue
        queue = manager.get_daily_queue()
        
        # Process a review
        manager.process_review(trigger_id, approved=True, notes="...")
    """
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._pending_triggers: Dict[str, HITLTrigger] = {}
        self._callbacks: Dict[TriggerType, List[Callable]] = {}
    
    def should_trigger_review(
        self,
        property_data: Dict[str, Any],
        ml_score: float = None,
        lien_count: int = None,
        anomaly_score: float = None,
    ) -> Optional[TriggerType]:
        """Check if a property/decision should trigger human review"""
        
        # Check high value
        value = property_data.get("market_value", 0) or property_data.get("just_value", 0)
        if value > HITL_THRESHOLDS["high_value_usd"]:
            return TriggerType.HIGH_VALUE
        
        # Check low confidence
        if ml_score is not None and ml_score < HITL_THRESHOLDS["low_confidence_score"]:
            return TriggerType.LOW_CONFIDENCE
        
        # Check complex liens
        liens = lien_count or property_data.get("lien_count", 0)
        if liens > HITL_THRESHOLDS["complex_liens_count"]:
            return TriggerType.COMPLEX_LIENS
        
        # Check anomaly
        if anomaly_score is not None and anomaly_score > HITL_THRESHOLDS["anomaly_score"]:
            return TriggerType.ANOMALY
        
        return None
    
    def create_trigger(
        self,
        trigger_type: TriggerType,
        title: str,
        description: str,
        data: Dict[str, Any],
        triggered_by: str = "system",
        priority: TriggerPriority = None,
    ) -> HITLTrigger:
        """Create a new HITL trigger"""
        
        # Auto-determine priority if not provided
        if priority is None:
            if trigger_type == TriggerType.SECURITY:
                priority = TriggerPriority.CRITICAL
            elif trigger_type == TriggerType.HIGH_VALUE:
                priority = TriggerPriority.HIGH
            elif trigger_type == TriggerType.LOW_CONFIDENCE:
                priority = TriggerPriority.MEDIUM
            else:
                priority = TriggerPriority.LOW
        
        # Calculate expiry
        if priority == TriggerPriority.CRITICAL:
            expiry_hours = HITL_THRESHOLDS["critical_expiry_hours"]
        elif priority == TriggerPriority.HIGH:
            expiry_hours = HITL_THRESHOLDS["high_priority_expiry_hours"]
        else:
            expiry_hours = HITL_THRESHOLDS["low_priority_expiry_hours"]
        
        trigger = HITLTrigger(
            id=f"hitl_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self._pending_triggers)}",
            trigger_type=trigger_type,
            priority=priority,
            status=TriggerStatus.PENDING,
            title=title,
            description=description,
            data=data,
            triggered_at=datetime.utcnow(),
            triggered_by=triggered_by,
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
        )
        
        self._pending_triggers[trigger.id] = trigger
        
        # Fire callbacks
        self._fire_callbacks(trigger)
        
        # Persist to Supabase
        self._persist_trigger(trigger)
        
        logger.info(f"HITL trigger created: {trigger.id} ({trigger_type.value})")
        return trigger
    
    def _fire_callbacks(self, trigger: HITLTrigger):
        """Fire registered callbacks for trigger type"""
        callbacks = self._callbacks.get(trigger.trigger_type, [])
        for callback in callbacks:
            try:
                callback(trigger)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _persist_trigger(self, trigger: HITLTrigger):
        """Save trigger to Supabase"""
        if self.supabase:
            try:
                self.supabase.table("hitl_triggers").insert(trigger.to_dict()).execute()
            except Exception as e:
                logger.error(f"Failed to persist trigger: {e}")
    
    def register_callback(self, trigger_type: TriggerType, callback: Callable):
        """Register a callback for trigger type"""
        if trigger_type not in self._callbacks:
            self._callbacks[trigger_type] = []
        self._callbacks[trigger_type].append(callback)
    
    def get_daily_queue(self, date: datetime = None) -> List[HITLTrigger]:
        """Get Ariel's daily review queue (max 10 items, 20 min total)"""
        if date is None:
            date = datetime.utcnow()
        
        # Filter pending triggers
        pending = [
            t for t in self._pending_triggers.values()
            if t.status == TriggerStatus.PENDING and not t.is_expired()
        ]
        
        # Sort by priority (lowest number = highest priority)
        pending.sort(key=lambda t: (t.priority.value, t.triggered_at))
        
        # Limit to max daily reviews
        max_reviews = HITL_THRESHOLDS["max_daily_reviews"]
        return pending[:max_reviews]
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of review queue"""
        queue = self.get_daily_queue()
        
        by_type = {}
        by_priority = {}
        
        for trigger in queue:
            t = trigger.trigger_type.value
            p = trigger.priority.name
            by_type[t] = by_type.get(t, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1
        
        estimated_time = len(queue) * HITL_THRESHOLDS["review_time_minutes"]
        
        return {
            "total_pending": len(queue),
            "by_type": by_type,
            "by_priority": by_priority,
            "estimated_review_time_minutes": estimated_time,
            "within_daily_limit": estimated_time <= 20,
        }
    
    def process_review(
        self,
        trigger_id: str,
        approved: bool,
        reviewer: str = "ariel",
        notes: str = None,
    ) -> HITLTrigger:
        """Process a human review decision"""
        if trigger_id not in self._pending_triggers:
            raise ValueError(f"Trigger not found: {trigger_id}")
        
        trigger = self._pending_triggers[trigger_id]
        trigger.status = TriggerStatus.APPROVED if approved else TriggerStatus.REJECTED
        trigger.reviewed_at = datetime.utcnow()
        trigger.reviewed_by = reviewer
        trigger.decision = "APPROVED" if approved else "REJECTED"
        trigger.notes = notes
        
        # Update in Supabase
        if self.supabase:
            try:
                self.supabase.table("hitl_triggers").update({
                    "status": trigger.status.value,
                    "reviewed_at": trigger.reviewed_at.isoformat(),
                    "reviewed_by": trigger.reviewed_by,
                    "decision": trigger.decision,
                    "notes": trigger.notes,
                }).eq("id", trigger_id).execute()
            except Exception as e:
                logger.error(f"Failed to update trigger: {e}")
        
        logger.info(f"HITL review processed: {trigger_id} -> {trigger.decision}")
        return trigger
    
    def auto_expire_triggers(self) -> List[str]:
        """Expire old triggers that weren't reviewed"""
        expired = []
        
        for trigger_id, trigger in list(self._pending_triggers.items()):
            if trigger.status == TriggerStatus.PENDING and trigger.is_expired():
                trigger.status = TriggerStatus.EXPIRED
                expired.append(trigger_id)
                
                # Low priority items auto-approve on expiry
                if trigger.priority in [TriggerPriority.LOW, TriggerPriority.MEDIUM]:
                    trigger.decision = "AUTO_APPROVED"
                    trigger.notes = "Auto-approved due to expiry without review"
                else:
                    trigger.decision = "ESCALATED"
                    trigger.notes = "High priority item expired - escalation required"
        
        return expired


# =============================================================================
# TRIGGER HELPER FUNCTIONS
# =============================================================================

def create_high_value_trigger(
    manager: HITLTriggerManager,
    property_data: Dict[str, Any],
    agent: str = "analysis_agent",
) -> HITLTrigger:
    """Create a high-value property trigger"""
    value = property_data.get("market_value", 0)
    return manager.create_trigger(
        trigger_type=TriggerType.HIGH_VALUE,
        title=f"High-Value Property: ${value:,.0f}",
        description=f"Property {property_data.get('account', 'N/A')} exceeds $500K threshold",
        data=property_data,
        triggered_by=agent,
        priority=TriggerPriority.HIGH,
    )


def create_low_confidence_trigger(
    manager: HITLTriggerManager,
    property_data: Dict[str, Any],
    ml_score: float,
    agent: str = "analysis_agent",
) -> HITLTrigger:
    """Create a low confidence ML score trigger"""
    return manager.create_trigger(
        trigger_type=TriggerType.LOW_CONFIDENCE,
        title=f"Low Confidence Score: {ml_score:.1f}%",
        description=f"ML score below 40% threshold for {property_data.get('account', 'N/A')}",
        data={**property_data, "ml_score": ml_score},
        triggered_by=agent,
        priority=TriggerPriority.MEDIUM,
    )


def create_complex_liens_trigger(
    manager: HITLTriggerManager,
    property_data: Dict[str, Any],
    lien_count: int,
    liens: List[Dict] = None,
    agent: str = "analysis_agent",
) -> HITLTrigger:
    """Create a complex liens trigger"""
    return manager.create_trigger(
        trigger_type=TriggerType.COMPLEX_LIENS,
        title=f"Complex Lien Structure: {lien_count} liens",
        description=f"Property {property_data.get('account', 'N/A')} has {lien_count} liens (>5 threshold)",
        data={**property_data, "lien_count": lien_count, "liens": liens or []},
        triggered_by=agent,
        priority=TriggerPriority.HIGH,
    )


def create_security_trigger(
    manager: HITLTriggerManager,
    alert_type: str,
    details: Dict[str, Any],
    agent: str = "system",
) -> HITLTrigger:
    """Create a security alert trigger"""
    return manager.create_trigger(
        trigger_type=TriggerType.SECURITY,
        title=f"Security Alert: {alert_type}",
        description=f"Security event detected requiring review",
        data=details,
        triggered_by=agent,
        priority=TriggerPriority.CRITICAL,
    )


# =============================================================================
# GLOBAL MANAGER INSTANCE
# =============================================================================

_hitl_manager: Optional[HITLTriggerManager] = None

def get_hitl_manager() -> HITLTriggerManager:
    """Get global HITL manager instance"""
    global _hitl_manager
    if _hitl_manager is None:
        _hitl_manager = HITLTriggerManager()
    return _hitl_manager


if __name__ == "__main__":
    # Demo usage
    manager = get_hitl_manager()
    
    # Test high value trigger
    trigger = create_high_value_trigger(
        manager,
        {"account": "2835546", "market_value": 750000, "address": "123 Test St"}
    )
    print(f"Created: {trigger.id}")
    
    # Get queue
    summary = manager.get_queue_summary()
    print(f"Queue: {summary}")
