#!/usr/bin/env python3
"""
Security Type Definitions
P5 Codebase: Complete type safety (+1.5 points)

Provides comprehensive type definitions for all security-related data structures.

Author: BidDeed.AI / Everest Capital USA
"""

from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod


# =============================================================================
# ENUMS
# =============================================================================

class SecurityEventType(Enum):
    """Types of security events"""
    INJECTION_ATTEMPT = "injection_attempt"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    ANOMALY_DETECTED = "anomaly_detected"
    POLICY_VIOLATION = "policy_violation"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    VALIDATION_FAILURE = "validation_failure"


class Severity(Enum):
    """Alert/event severity levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class ValidationStatus(Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class HITLDecisionStatus(Enum):
    """HITL decision statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class PrivilegeLevel(Enum):
    """Database privilege levels"""
    NONE = 0
    SELECT = 1
    INSERT = 2
    UPDATE = 3
    DELETE = 4
    ALL = 5


# =============================================================================
# BASE TYPES
# =============================================================================

@dataclass
class BaseEvent:
    """Base class for all events"""
    event_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityEvent(BaseEvent):
    """Security-specific event"""
    event_type: SecurityEventType
    severity: Severity
    description: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None


# =============================================================================
# VALIDATION TYPES
# =============================================================================

@dataclass
class ValidationRule:
    """Definition of a validation rule"""
    rule_id: str
    name: str
    pattern: Optional[str] = None
    check_type: str = "regex"
    severity: Severity = Severity.MEDIUM
    message: str = ""
    enabled: bool = True


@dataclass
class ValidationViolation:
    """A single validation violation"""
    rule_id: str
    field: str
    value: Any
    message: str
    severity: Severity
    position: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of validation check"""
    status: ValidationStatus
    violations: List[ValidationViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    
    @property
    def is_valid(self) -> bool:
        return self.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]
    
    @property
    def has_critical(self) -> bool:
        return any(v.severity == Severity.CRITICAL for v in self.violations)


# =============================================================================
# INPUT/OUTPUT VALIDATION
# =============================================================================

@dataclass
class InputValidationConfig:
    """Configuration for input validation"""
    max_length: int = 10000
    allowed_characters: Optional[str] = None
    blocked_patterns: List[str] = field(default_factory=list)
    sanitize_html: bool = True
    check_injection: bool = True
    check_encoding: bool = True


@dataclass
class OutputValidationConfig:
    """Configuration for output validation"""
    max_length: int = 50000
    redact_patterns: List[str] = field(default_factory=list)
    check_pii: bool = True
    check_secrets: bool = True
    check_urls: bool = True


@dataclass
class SensitiveDataMatch:
    """A match of sensitive data in content"""
    pattern_name: str
    pattern_type: str
    matched_value: str
    redacted_value: str
    position: int
    length: int
    severity: Severity


# =============================================================================
# CIRCUIT BREAKER TYPES
# =============================================================================

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 30
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerState:
    """Current state of a circuit breaker"""
    name: str
    state: CircuitState
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change: Optional[datetime] = None


# =============================================================================
# HITL TYPES
# =============================================================================

@dataclass
class HITLThresholds:
    """Thresholds for HITL triggers"""
    high_value_amount: float = 500000.0
    low_confidence_percent: float = 40.0
    complex_liens_count: int = 5
    decision_timeout_hours: int = 24
    auto_approve_below: float = 100000.0
    min_confidence_for_auto: float = 70.0


@dataclass
class HITLDecision:
    """A decision requiring human review"""
    decision_id: str
    trigger_type: str
    status: HITLDecisionStatus
    title: str
    description: str
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_notes: Optional[str] = None
    priority: int = 5  # 1=highest, 10=lowest


@dataclass
class HITLAuditEntry:
    """Audit trail entry for HITL decision"""
    entry_id: str
    decision_id: str
    action: str
    actor: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# PRIVILEGE TYPES
# =============================================================================

@dataclass
class ServiceAccountConfig:
    """Service account configuration"""
    name: str
    role: str
    tables: List[str]
    allowed_operations: List[str]
    max_privilege: PrivilegeLevel
    row_filter: Optional[str] = None


@dataclass
class RLSPolicy:
    """Row Level Security policy definition"""
    policy_name: str
    table_name: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE, ALL
    using_expression: str
    with_check: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: ["authenticated"])


@dataclass
class PrivilegeViolation:
    """A detected privilege violation"""
    violation_id: str
    agent: str
    table: str
    operation: str
    expected: str
    actual: str
    risk_level: Severity
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditResult:
    """Result of a privilege audit"""
    audit_id: str
    passed: bool
    score: int
    total_checks: int
    passed_checks: int
    violations: List[PrivilegeViolation]
    recommendations: List[str]
    audited_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# ALERT TYPES
# =============================================================================

@dataclass
class AlertRule:
    """Rule for generating alerts"""
    rule_id: str
    name: str
    condition: str
    severity: Severity
    channels: List[str]
    cooldown_minutes: int = 5
    enabled: bool = True


@dataclass
class Alert:
    """A generated alert"""
    alert_id: str
    rule_id: str
    severity: Severity
    title: str
    description: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# METRICS TYPES
# =============================================================================

@dataclass
class SecurityMetric:
    """A security metric measurement"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SecurityDashboardData:
    """Data for security dashboard"""
    total_events_24h: int
    critical_events_24h: int
    active_alerts: int
    pending_hitl_decisions: int
    circuit_breakers_open: int
    last_audit_score: int
    metrics: List[SecurityMetric] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# TYPE ALIASES
# =============================================================================

JSONSerializable = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
SecurityContext = Dict[str, Any]
ValidationCallback = callable
T = TypeVar('T')


# =============================================================================
# PROTOCOLS / INTERFACES
# =============================================================================

class Validator(ABC):
    """Abstract base class for validators"""
    
    @abstractmethod
    def validate(self, content: str, context: SecurityContext = None) -> ValidationResult:
        """Validate content and return result"""
        pass


class AlertDispatcher(ABC):
    """Abstract base class for alert dispatchers"""
    
    @abstractmethod
    async def dispatch(self, alert: Alert) -> bool:
        """Dispatch an alert and return success status"""
        pass
