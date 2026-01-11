"""
BidDeed.AI Success Criteria Validator
Validates stage outputs against defined success criteria from success_criteria.json

This implements the "Ralph Wiggum pattern" - continuous validation until
criteria met, inspired by the autonomous agent loop concept.

Created by: Ariel Shapira, Solo Founder - Everest Capital USA
Architecture: Success-Criteria-Driven Development
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ValidationSeverity(Enum):
    """Severity levels for validation failures"""
    CRITICAL = "critical"  # Must fix - blocks progress
    WARNING = "warning"    # Should fix - doesn't block
    INFO = "info"          # Nice to have


@dataclass
class ValidationResult:
    """Result from a single validation check"""
    check_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'check_name': self.check_name,
            'passed': self.passed,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StageValidationReport:
    """Validation report for a complete stage"""
    stage_name: str
    validation_results: List[ValidationResult]
    all_critical_passed: bool
    all_warnings_passed: bool
    iteration_number: int
    retry_required: bool
    retry_instructions: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        """Stage passes if all critical checks pass"""
        return self.all_critical_passed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stage_name': self.stage_name,
            'iteration': self.iteration_number,
            'passed': self.passed,
            'all_critical_passed': self.all_critical_passed,
            'all_warnings_passed': self.all_warnings_passed,
            'retry_required': self.retry_required,
            'retry_instructions': self.retry_instructions,
            'checks': [v.to_dict() for v in self.validation_results],
            'summary': {
                'total_checks': len(self.validation_results),
                'passed': sum(1 for v in self.validation_results if v.passed),
                'failed': sum(1 for v in self.validation_results if not v.passed),
                'critical_failures': sum(
                    1 for v in self.validation_results 
                    if not v.passed and v.severity == ValidationSeverity.CRITICAL
                )
            }
        }


class SuccessCriteriaValidator:
    """
    Validates stage outputs against success criteria.
    
    This is the core validation engine that implements the Ralph-like
    loop pattern - keeps validating until criteria met or max iterations.
    """
    
    def __init__(self, criteria_path: str = "success_criteria.json"):
        self.criteria_path = Path(criteria_path)
        self.criteria = self._load_criteria()
        
    def _load_criteria(self) -> Dict[str, Any]:
        """Load success criteria from JSON file"""
        if not self.criteria_path.exists():
            raise FileNotFoundError(f"Success criteria not found: {self.criteria_path}")
        
        with open(self.criteria_path) as f:
            return json.load(f)
    
    def validate_stage(
        self,
        stage_name: str,
        stage_output: Dict[str, Any],
        iteration: int = 1,
        context: Optional[Dict[str, Any]] = None
    ) -> StageValidationReport:
        """
        Validate a stage's output against its success criteria.
        
        Args:
            stage_name: Name of stage (e.g., "discovery", "lien_priority")
            stage_output: Output data from the stage
            iteration: Current iteration number (for retry tracking)
            context: Additional context (property data, global state, etc.)
        
        Returns:
            StageValidationReport with validation results
        """
        if stage_name not in self.criteria['stages']:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        stage_criteria = self.criteria['stages'][stage_name]
        results = []
        
        # Validate required outputs
        results.extend(self._validate_required_outputs(
            stage_criteria.get('required_outputs', []),
            stage_output
        ))
        
        # Validate quality gates
        results.extend(self._validate_quality_gates(
            stage_criteria.get('quality_gates', {}),
            stage_output,
            context or {}
        ))
        
        # Validate performance criteria
        if 'performance' in stage_criteria and context:
            results.extend(self._validate_performance(
                stage_criteria['performance'],
                context
            ))
        
        # Check evaluators (if post-auction validation)
        if 'evaluators' in stage_criteria and context and context.get('post_auction_data'):
            results.extend(self._run_evaluators(
                stage_criteria['evaluators'],
                stage_output,
                context['post_auction_data']
            ))
        
        # Determine if retry needed
        critical_failures = [r for r in results if not r.passed and r.severity == ValidationSeverity.CRITICAL]
        all_critical_passed = len(critical_failures) == 0
        all_warnings_passed = all(r.passed or r.severity != ValidationSeverity.WARNING for r in results)
        
        retry_required = not all_critical_passed and iteration < 5
        retry_instructions = self._generate_retry_instructions(critical_failures) if retry_required else None
        
        return StageValidationReport(
            stage_name=stage_name,
            validation_results=results,
            all_critical_passed=all_critical_passed,
            all_warnings_passed=all_warnings_passed,
            iteration_number=iteration,
            retry_required=retry_required,
            retry_instructions=retry_instructions
        )
    
    def _validate_required_outputs(
        self,
        required: List[str],
        output: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate that all required output fields are present"""
        results = []
        
        for field in required:
            present = field in output and output[field] is not None
            
            results.append(ValidationResult(
                check_name=f"required_output_{field}",
                passed=present,
                severity=ValidationSeverity.CRITICAL,
                message=f"Required field '{field}' {'present' if present else 'MISSING'}",
                details={'field': field, 'value': output.get(field)}
            ))
        
        return results
    
    def _validate_quality_gates(
        self,
        gates: Dict[str, Dict],
        output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate quality gates based on validation type"""
        results = []
        
        for gate_name, gate_config in gates.items():
            validation_type = gate_config.get('validation')
            is_critical = gate_config.get('critical', False)
            severity = ValidationSeverity.CRITICAL if is_critical else ValidationSeverity.WARNING
            
            # Dispatch to appropriate validator
            if validation_type == 'unique_case_numbers':
                result = self._validate_unique_case_numbers(output, gate_name, severity)
            elif validation_type == 'regex_match':
                result = self._validate_regex(output, gate_config, gate_name, severity)
            elif validation_type == 'date_validation':
                result = self._validate_date(output, gate_config, gate_name, severity)
            elif validation_type == 'source_verification':
                result = self._validate_source(output, gate_config, gate_name, severity)
            elif validation_type == 'type_check':
                result = self._validate_type(output, gate_config, gate_name, severity)
            elif validation_type == 'enum_check':
                result = self._validate_enum(output, gate_config, gate_name, severity)
            elif validation_type == 'range_check':
                result = self._validate_range(output, gate_config, gate_name, severity)
            elif validation_type == 'formula_check':
                result = self._validate_formula(output, gate_config, gate_name, severity)
            elif validation_type == 'threshold_check':
                result = self._validate_threshold(output, gate_config, gate_name, severity)
            elif validation_type == 'file_check':
                result = self._validate_file(output, gate_config, gate_name, severity)
            elif validation_type == 'text_scan':
                result = self._validate_text_scan(output, gate_config, gate_name, severity)
            elif validation_type == 'database_check':
                result = self._validate_database(output, context, gate_config, gate_name, severity)
            else:
                result = ValidationResult(
                    check_name=gate_name,
                    passed=True,
                    severity=ValidationSeverity.INFO,
                    message=f"Validation type '{validation_type}' not implemented - skipping"
                )
            
            results.append(result)
        
        return results
    
    def _validate_performance(
        self,
        perf_criteria: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate performance metrics"""
        results = []
        
        if 'max_duration_seconds' in perf_criteria:
            duration = context.get('duration_seconds', 0)
            max_duration = perf_criteria['max_duration_seconds']
            passed = duration <= max_duration
            
            results.append(ValidationResult(
                check_name='performance_duration',
                passed=passed,
                severity=ValidationSeverity.WARNING,
                message=f"Duration {duration}s {'within' if passed else 'EXCEEDS'} limit of {max_duration}s",
                details={'duration': duration, 'limit': max_duration}
            ))
        
        if 'max_api_calls' in perf_criteria:
            api_calls = context.get('api_calls', 0)
            max_calls = perf_criteria['max_api_calls']
            passed = api_calls <= max_calls
            
            results.append(ValidationResult(
                check_name='performance_api_calls',
                passed=passed,
                severity=ValidationSeverity.WARNING,
                message=f"API calls {api_calls} {'within' if passed else 'EXCEEDS'} limit of {max_calls}",
                details={'api_calls': api_calls, 'limit': max_calls}
            ))
        
        return results
    
    def _run_evaluators(
        self,
        evaluator_names: List[str],
        predicted: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Run evaluators from evaluations.py against actual results"""
        # This integrates with existing evaluations.py framework
        # For now, return placeholder - will integrate when actual data available
        return [
            ValidationResult(
                check_name=f"evaluator_{name}",
                passed=True,
                severity=ValidationSeverity.INFO,
                message=f"Evaluator '{name}' will run post-auction",
                details={'evaluator': name, 'status': 'pending_actual_data'}
            )
            for name in evaluator_names
        ]
    
    # ============================================
    # SPECIFIC VALIDATORS
    # ============================================
    
    def _validate_unique_case_numbers(
        self,
        output: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate case numbers are unique"""
        case_numbers = output.get('case_numbers', [])
        unique_count = len(set(case_numbers))
        total_count = len(case_numbers)
        passed = unique_count == total_count
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Case numbers: {unique_count} unique out of {total_count} total",
            details={
                'unique': unique_count,
                'total': total_count,
                'duplicates': total_count - unique_count
            }
        )
    
    def _validate_regex(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate field matches regex pattern"""
        field = check_name.replace('_', ' ').split()[-1]  # Extract field name
        value = output.get('case_numbers', [''])[0] if 'case' in check_name else ''
        pattern = config.get('pattern', '')
        
        if isinstance(value, list):
            matches = [bool(re.match(pattern, str(v))) for v in value]
            passed = all(matches)
            match_count = sum(matches)
        else:
            passed = bool(re.match(pattern, str(value)))
            match_count = 1 if passed else 0
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Regex validation: {match_count}/{len(value) if isinstance(value, list) else 1} match",
            details={'pattern': pattern, 'value': value}
        )
    
    def _validate_date(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate date field"""
        auction_date_str = output.get('auction_date', '')
        
        try:
            from datetime import timezone
            auction_date = datetime.fromisoformat(auction_date_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            passed = auction_date > now
            
            return ValidationResult(
                check_name=check_name,
                passed=passed,
                severity=severity,
                message=f"Auction date {auction_date.date()} is {'valid (future)' if passed else 'INVALID (past)'}",
                details={'auction_date': auction_date_str, 'current_date': now.isoformat()}
            )
        except (ValueError, AttributeError):
            return ValidationResult(
                check_name=check_name,
                passed=False,
                severity=severity,
                message=f"Invalid date format: {auction_date_str}",
                details={'value': auction_date_str}
            )
    
    def _validate_source(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate data source attribution"""
        source_field = output.get('data_source', output.get('source', ''))
        required_source = config.get('source', '')
        passed = required_source.upper() in str(source_field).upper()
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Source verification: {'VERIFIED' if passed else 'FAILED'} from {required_source}",
            details={'expected_source': required_source, 'actual_source': source_field}
        )
    
    def _validate_type(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate data type and range"""
        field = 'judgment_amount'  # Infer from context
        value = output.get(field)
        expected_type = config.get('data_type', 'float')
        min_value = config.get('min_value')
        
        if expected_type == 'float':
            try:
                float_value = float(value)
                type_ok = True
                range_ok = float_value >= min_value if min_value is not None else True
                passed = type_ok and range_ok
            except (ValueError, TypeError):
                passed = False
                float_value = None
        else:
            passed = isinstance(value, eval(expected_type))
            float_value = value
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Type check: {field} = {value} ({'OK' if passed else 'FAILED'})",
            details={'field': field, 'value': value, 'expected_type': expected_type}
        )
    
    def _validate_enum(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate value is in allowed enum"""
        value = output.get('final_recommendation', output.get('recommendation', ''))
        allowed = config.get('allowed_values', [])
        passed = value in allowed
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Enum check: '{value}' {'valid' if passed else 'INVALID'}",
            details={'value': value, 'allowed': allowed}
        )
    
    def _validate_range(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate numeric range"""
        value = output.get('third_party_probability', output.get('probability', 0))
        min_val = config.get('min', 0)
        max_val = config.get('max', 1)
        
        try:
            float_value = float(value)
            passed = min_val <= float_value <= max_val
        except (ValueError, TypeError):
            passed = False
            float_value = None
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Range check: {value} {'within' if passed else 'OUTSIDE'} [{min_val}, {max_val}]",
            details={'value': value, 'min': min_val, 'max': max_val}
        )
    
    def _validate_formula(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate calculation formula"""
        arv = output.get('arv_estimate', 0)
        repairs = output.get('repair_estimate', 0)
        max_bid = output.get('max_bid_amount', 0)
        
        # Formula: (ARV×70%)-Repairs-$10K-MIN($25K,15%ARV)
        expected = (arv * 0.70) - repairs - 10000 - min(25000, arv * 0.15)
        tolerance = 100  # $100 tolerance for rounding
        passed = abs(max_bid - expected) <= tolerance
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Formula check: max_bid={max_bid}, expected={expected:.0f}, diff={abs(max_bid - expected):.0f}",
            details={
                'max_bid': max_bid,
                'expected': expected,
                'arv': arv,
                'repairs': repairs,
                'difference': abs(max_bid - expected)
            }
        )
    
    def _validate_threshold(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate threshold-based classification"""
        ratio = output.get('bid_judgment_ratio', 0)
        recommendation = output.get('final_recommendation', '')
        thresholds = config.get('thresholds', {})
        
        # Determine expected recommendation based on ratio
        if ratio >= thresholds.get('BID', 0.75):
            expected = 'BID'
        elif ratio >= thresholds.get('REVIEW', 0.60):
            expected = 'REVIEW'
        else:
            expected = 'SKIP'
        
        passed = recommendation == expected
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Threshold check: ratio={ratio:.2f}, recommendation={recommendation}, expected={expected}",
            details={
                'ratio': ratio,
                'recommendation': recommendation,
                'expected': expected,
                'thresholds': thresholds
            }
        )
    
    def _validate_file(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate file exists and is readable"""
        file_path = output.get('docx_report', output.get('report_path', ''))
        
        if file_path and Path(file_path).exists():
            passed = True
            message = f"File exists: {file_path}"
        else:
            passed = False
            message = f"File NOT FOUND: {file_path}"
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=message,
            details={'file_path': file_path}
        )
    
    def _validate_text_scan(
        self,
        output: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Scan text for forbidden terms"""
        text = str(output)  # Convert entire output to string for scanning
        forbidden = config.get('forbidden_terms', [])
        found_terms = [term for term in forbidden if term in text]
        passed = len(found_terms) == 0
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Text scan: {'CLEAN' if passed else 'FOUND FORBIDDEN TERMS'}",
            details={'forbidden_terms': forbidden, 'found': found_terms}
        )
    
    def _validate_database(
        self,
        output: Dict,
        context: Dict,
        config: Dict,
        check_name: str,
        severity: ValidationSeverity
    ) -> ValidationResult:
        """Validate database operations (placeholder - requires Supabase client)"""
        table = config.get('table', '')
        # This will be implemented with actual Supabase client
        # For now, assume passed if output has 'supabase_logged' flag
        passed = output.get('supabase_logged', False)
        
        return ValidationResult(
            check_name=check_name,
            passed=passed,
            severity=severity,
            message=f"Database check: {table} {'LOGGED' if passed else 'NOT LOGGED'}",
            details={'table': table, 'logged': passed}
        )
    
    def _generate_retry_instructions(
        self,
        failures: List[ValidationResult]
    ) -> str:
        """Generate human-readable retry instructions"""
        instructions = ["RETRY REQUIRED - Fix these critical issues:\n"]
        
        for i, failure in enumerate(failures, 1):
            instructions.append(
                f"{i}. {failure.check_name}: {failure.message}"
            )
        
        return "\n".join(instructions)


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def validate_stage_output(
    stage_name: str,
    output: Dict[str, Any],
    iteration: int = 1,
    criteria_path: str = "success_criteria.json"
) -> StageValidationReport:
    """
    Convenience function to validate a stage output.
    
    Usage:
        report = validate_stage_output('lien_priority', stage_output, iteration=2)
        if report.passed:
            print("Stage passed!")
        else:
            print(f"Retry needed: {report.retry_instructions}")
    """
    validator = SuccessCriteriaValidator(criteria_path)
    return validator.validate_stage(stage_name, output, iteration)


if __name__ == "__main__":
    # Example usage
    validator = SuccessCriteriaValidator("success_criteria.json")
    
    # Test discovery stage
    discovery_output = {
        'auction_date': '2026-02-03T11:00:00Z',
        'properties_list': [{'case': '05-2024-CA-123456-XXXX-XX'}],
        'case_numbers': ['05-2024-CA-123456-XXXX-XX'],
        'plaintiff_names': ['WELLS FARGO BANK']
    }
    
    report = validator.validate_stage('discovery', discovery_output, iteration=1)
    print(json.dumps(report.to_dict(), indent=2))
