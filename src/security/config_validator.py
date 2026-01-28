#!/usr/bin/env python3
"""
Security Configuration Validator
P6 Security: Configuration management (+2 points)

Validates all security configurations at runtime, detects configuration drift,
and enforces security baselines.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfigStatus(Enum):
    """Configuration validation status"""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    INSECURE = "insecure"
    DRIFT = "drift"


class SecurityLevel(Enum):
    """Security requirement levels"""
    CRITICAL = 1  # Must be set correctly
    HIGH = 2      # Should be set correctly
    MEDIUM = 3    # Recommended
    LOW = 4       # Optional


@dataclass
class ConfigRequirement:
    """Security configuration requirement"""
    name: str
    env_var: str
    level: SecurityLevel
    description: str
    pattern: Optional[str] = None  # Regex pattern for validation
    min_length: Optional[int] = None
    default: Optional[str] = None
    sensitive: bool = True
    
    def validate(self, value: Optional[str]) -> Tuple[ConfigStatus, str]:
        """Validate a configuration value"""
        if value is None:
            if self.level == SecurityLevel.CRITICAL:
                return ConfigStatus.MISSING, f"Critical config {self.name} is missing"
            elif self.default:
                return ConfigStatus.VALID, f"Using default for {self.name}"
            return ConfigStatus.MISSING, f"Config {self.name} not set"
        
        if self.min_length and len(value) < self.min_length:
            return ConfigStatus.INSECURE, f"{self.name} too short (min {self.min_length})"
        
        if self.pattern and not re.match(self.pattern, value):
            return ConfigStatus.INVALID, f"{self.name} doesn't match required pattern"
        
        return ConfigStatus.VALID, "OK"


@dataclass
class SecurityBaseline:
    """Security baseline configuration"""
    version: str
    requirements: List[ConfigRequirement]
    checksum: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def compute_checksum(self) -> str:
        """Compute baseline checksum for drift detection"""
        data = json.dumps([r.name for r in self.requirements], sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    results: Dict[str, Tuple[ConfigStatus, str]]
    baseline_drift: bool = False
    validated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "critical_failures": self.critical_failures,
            "baseline_drift": self.baseline_drift,
            "validated_at": self.validated_at.isoformat(),
            "results": {k: {"status": v[0].value, "message": v[1]} for k, v in self.results.items()},
        }


# Default security baseline for SPD
DEFAULT_SECURITY_BASELINE = SecurityBaseline(
    version="1.0.0",
    requirements=[
        # Critical - Must be set
        ConfigRequirement(
            name="Supabase URL",
            env_var="SUPABASE_URL",
            level=SecurityLevel.CRITICAL,
            description="Supabase project URL",
            pattern=r"^https://.*\.supabase\.co$",
        ),
        ConfigRequirement(
            name="Supabase Service Key",
            env_var="SUPABASE_SERVICE_ROLE_KEY",
            level=SecurityLevel.CRITICAL,
            description="Supabase service role key",
            min_length=100,
            pattern=r"^eyJ.*",
        ),
        ConfigRequirement(
            name="Encryption Key",
            env_var="ENCRYPTION_KEY",
            level=SecurityLevel.CRITICAL,
            description="AES-256 encryption key",
            min_length=32,
        ),
        
        # High - Should be set
        ConfigRequirement(
            name="JWT Secret",
            env_var="JWT_SECRET",
            level=SecurityLevel.HIGH,
            description="JWT signing secret",
            min_length=32,
        ),
        ConfigRequirement(
            name="Slack Security Webhook",
            env_var="SLACK_SECURITY_WEBHOOK",
            level=SecurityLevel.HIGH,
            description="Slack webhook for security alerts",
            pattern=r"^https://hooks\.slack\.com/.*",
        ),
        ConfigRequirement(
            name="API Rate Limit",
            env_var="API_RATE_LIMIT",
            level=SecurityLevel.HIGH,
            description="API rate limit per minute",
            default="60",
        ),
        
        # Medium - Recommended
        ConfigRequirement(
            name="LLM API Key",
            env_var="ANTHROPIC_API_KEY",
            level=SecurityLevel.MEDIUM,
            description="Anthropic API key",
            pattern=r"^sk-ant-.*",
        ),
        ConfigRequirement(
            name="Log Level",
            env_var="LOG_LEVEL",
            level=SecurityLevel.MEDIUM,
            description="Logging level",
            default="INFO",
        ),
        ConfigRequirement(
            name="Environment",
            env_var="ENVIRONMENT",
            level=SecurityLevel.MEDIUM,
            description="Deployment environment",
            default="production",
        ),
        
        # Low - Optional
        ConfigRequirement(
            name="Debug Mode",
            env_var="DEBUG",
            level=SecurityLevel.LOW,
            description="Debug mode (should be false in production)",
            default="false",
        ),
    ],
)


class ConfigValidator:
    """
    Validates security configurations at runtime.
    
    Usage:
        validator = ConfigValidator()
        result = validator.validate_all()
        
        if not result.passed:
            print(f"Failed checks: {result.failed_checks}")
            for name, (status, msg) in result.results.items():
                if status != ConfigStatus.VALID:
                    print(f"  {name}: {msg}")
    """
    
    def __init__(self, baseline: SecurityBaseline = None):
        self.baseline = baseline or DEFAULT_SECURITY_BASELINE
        self._stored_checksum: Optional[str] = None
    
    def validate_all(self) -> ValidationResult:
        """Validate all security configurations"""
        results: Dict[str, Tuple[ConfigStatus, str]] = {}
        passed = 0
        failed = 0
        critical_failures = 0
        
        for req in self.baseline.requirements:
            value = os.environ.get(req.env_var)
            status, message = req.validate(value)
            results[req.name] = (status, message)
            
            if status == ConfigStatus.VALID:
                passed += 1
            else:
                failed += 1
                if req.level == SecurityLevel.CRITICAL:
                    critical_failures += 1
        
        # Check for baseline drift
        current_checksum = self.baseline.compute_checksum()
        drift = self._stored_checksum is not None and current_checksum != self._stored_checksum
        
        return ValidationResult(
            passed=critical_failures == 0 and failed <= 2,
            total_checks=len(self.baseline.requirements),
            passed_checks=passed,
            failed_checks=failed,
            critical_failures=critical_failures,
            results=results,
            baseline_drift=drift,
        )
    
    def validate_environment(self) -> Dict[str, bool]:
        """Quick validation of environment variables"""
        return {
            req.name: os.environ.get(req.env_var) is not None
            for req in self.baseline.requirements
        }
    
    def check_baseline_compliance(self) -> bool:
        """Ensure security baseline compliance"""
        result = self.validate_all()
        return result.passed and not result.baseline_drift
    
    def get_missing_critical(self) -> List[str]:
        """Get list of missing critical configurations"""
        missing = []
        for req in self.baseline.requirements:
            if req.level == SecurityLevel.CRITICAL:
                if os.environ.get(req.env_var) is None:
                    missing.append(req.env_var)
        return missing
    
    def check_insecure_defaults(self) -> List[str]:
        """Check for insecure default values in production"""
        warnings = []
        
        if os.environ.get("DEBUG", "").lower() in ["true", "1", "yes"]:
            warnings.append("DEBUG mode enabled in production")
        
        if os.environ.get("ENVIRONMENT", "") == "development":
            warnings.append("Running in development environment")
        
        if os.environ.get("LOG_LEVEL", "").upper() == "DEBUG":
            warnings.append("DEBUG logging may expose sensitive data")
        
        return warnings
    
    def export_baseline(self) -> Dict[str, Any]:
        """Export current baseline for storage"""
        return {
            "version": self.baseline.version,
            "checksum": self.baseline.compute_checksum(),
            "requirements": [
                {
                    "name": r.name,
                    "env_var": r.env_var,
                    "level": r.level.name,
                    "required": r.level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH],
                }
                for r in self.baseline.requirements
            ],
            "exported_at": datetime.utcnow().isoformat(),
        }
    
    def store_baseline_checksum(self):
        """Store current checksum for drift detection"""
        self._stored_checksum = self.baseline.compute_checksum()


def validate_config() -> ValidationResult:
    """Convenience function to validate configuration"""
    validator = ConfigValidator()
    return validator.validate_all()


def check_security_config() -> bool:
    """Quick security config check - returns True if safe to proceed"""
    validator = ConfigValidator()
    result = validator.validate_all()
    
    if result.critical_failures > 0:
        logger.error(f"Critical security config failures: {result.critical_failures}")
        return False
    
    if result.baseline_drift:
        logger.warning("Security baseline drift detected")
    
    return result.passed


if __name__ == "__main__":
    result = validate_config()
    print(f"Validation {'PASSED' if result.passed else 'FAILED'}")
    print(f"Checks: {result.passed_checks}/{result.total_checks}")
    print(f"Critical failures: {result.critical_failures}")
