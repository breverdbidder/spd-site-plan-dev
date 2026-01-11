"""
BidDeed.AI Ralph Orchestrator
Autonomous loop executor inspired by the "Ralph Wiggum pattern"

Continuously executes stages until success criteria met or max iterations reached.
Integrates with Smart Router for 90% FREE tier processing.

Created by: Ariel Shapira, Solo Founder - Everest Capital USA
Architecture: Autonomous Agent Loop with Success-Criteria Validation
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid

from success_criteria_validator import (
    SuccessCriteriaValidator,
    StageValidationReport,
    ValidationSeverity
)


class LoopStatus(Enum):
    """Status of the autonomous loop"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    VALIDATING = "validating"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations_reached"


@dataclass
class IterationMetrics:
    """Metrics for a single iteration"""
    iteration_number: int
    stage_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    api_calls: int = 0
    cost_estimate: float = 0.0
    smart_router_tier: str = "FREE"
    validation_passed: bool = False
    retry_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'iteration': self.iteration_number,
            'stage': self.stage_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'api_calls': self.api_calls,
            'cost_estimate': self.cost_estimate,
            'smart_router_tier': self.smart_router_tier,
            'validation_passed': self.validation_passed,
            'retry_required': self.retry_required
        }


@dataclass
class RalphLoopState:
    """State for the autonomous Ralph loop"""
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: LoopStatus = LoopStatus.INITIALIZING
    current_iteration: int = 0
    max_iterations: int = 30
    stage_name: str = ""
    stage_output: Dict[str, Any] = field(default_factory=dict)
    validation_history: List[StageValidationReport] = field(default_factory=list)
    iteration_metrics: List[IterationMetrics] = field(default_factory=list)
    total_cost: float = 0.0
    total_api_calls: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'loop_id': self.loop_id,
            'status': self.status.value,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
            'stage_name': self.stage_name,
            'total_cost': self.total_cost,
            'total_api_calls': self.total_api_calls,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': (self.completed_at - self.started_at).total_seconds() if self.completed_at and self.started_at else 0,
            'validation_history_count': len(self.validation_history),
            'iterations_completed': len(self.iteration_metrics),
            'error_message': self.error_message
        }


class RalphOrchestrator:
    """
    Autonomous loop orchestrator implementing the Ralph pattern.
    
    Executes a stage repeatedly until success criteria met:
    1. Execute stage logic
    2. Validate output against success criteria  
    3. If validation fails and iterations remain: retry with corrections
    4. If validation passes: return result
    5. If max iterations: return partial result with failure report
    
    Integrates with Smart Router for cost optimization (90% FREE tier target).
    """
    
    def __init__(
        self,
        criteria_path: str = "success_criteria.json",
        smart_router = None,  # Smart Router instance
        supabase_client = None,  # Supabase client for logging
        verbose: bool = True
    ):
        self.validator = SuccessCriteriaValidator(criteria_path)
        self.smart_router = smart_router
        self.supabase = supabase_client
        self.verbose = verbose
        
        # Load criteria for default max_iterations
        self.criteria = self.validator.criteria
        self.default_max_iterations = self.criteria.get('iteration_limits', {}).get(
            'max_total_iterations', 30
        )
    
    async def execute_stage_loop(
        self,
        stage_name: str,
        stage_executor: Callable[[Dict[str, Any], int], Dict[str, Any]],
        initial_input: Dict[str, Any],
        max_iterations: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any], RalphLoopState]:
        """
        Execute a stage with autonomous retry loop until success criteria met.
        
        Args:
            stage_name: Name of stage (e.g., "lien_priority")
            stage_executor: Async function that executes stage logic
                           Signature: async def execute(input_data, iteration) -> output_data
            initial_input: Initial input data for the stage
            max_iterations: Max iterations (default from criteria)
            context: Additional context (property data, global state, etc.)
        
        Returns:
            Tuple of (success, final_output, loop_state)
        """
        max_iter = max_iterations or self.default_max_iterations
        loop_state = RalphLoopState(
            stage_name=stage_name,
            max_iterations=max_iter,
            started_at=datetime.utcnow()
        )
        
        self._log(f"🚀 Starting Ralph loop for stage: {stage_name}")
        self._log(f"   Max iterations: {max_iter}")
        
        current_input = initial_input.copy()
        
        for iteration in range(1, max_iter + 1):
            loop_state.status = LoopStatus.RUNNING
            loop_state.current_iteration = iteration
            
            self._log(f"\n📍 Iteration {iteration}/{max_iter}")
            
            # Execute stage
            metrics = IterationMetrics(
                iteration_number=iteration,
                stage_name=stage_name,
                started_at=datetime.utcnow()
            )
            
            try:
                # Execute stage logic
                stage_output = await self._execute_with_router(
                    stage_executor,
                    current_input,
                    iteration,
                    stage_name,
                    metrics
                )
                
                metrics.completed_at = datetime.utcnow()
                metrics.duration_seconds = (metrics.completed_at - metrics.started_at).total_seconds()
                
                loop_state.stage_output = stage_output
                
                # Validate output
                loop_state.status = LoopStatus.VALIDATING
                validation_report = self.validator.validate_stage(
                    stage_name,
                    stage_output,
                    iteration,
                    context or {}
                )
                
                loop_state.validation_history.append(validation_report)
                metrics.validation_passed = validation_report.passed
                metrics.retry_required = validation_report.retry_required
                
                self._log(f"   ✓ Execution completed in {metrics.duration_seconds:.1f}s")
                self._log(f"   ✓ Validation: {'PASSED ✅' if validation_report.passed else 'FAILED ❌'}")
                
                if validation_report.passed:
                    # Success! Stage passed all criteria
                    loop_state.status = LoopStatus.COMPLETED
                    loop_state.completed_at = datetime.utcnow()
                    loop_state.final_result = stage_output
                    loop_state.iteration_metrics.append(metrics)
                    
                    self._log(f"\n🎉 SUCCESS! Stage '{stage_name}' completed in {iteration} iteration(s)")
                    self._log_validation_summary(validation_report)
                    
                    # Log to Supabase
                    await self._log_to_supabase(loop_state, validation_report)
                    
                    return True, stage_output, loop_state
                
                elif validation_report.retry_required:
                    # Failed but can retry
                    loop_state.status = LoopStatus.RETRYING
                    loop_state.iteration_metrics.append(metrics)
                    
                    self._log(f"   ⚠️  Validation failed - retry required")
                    self._log_validation_summary(validation_report)
                    
                    # Prepare retry with corrections
                    current_input = self._prepare_retry_input(
                        current_input,
                        stage_output,
                        validation_report
                    )
                    
                    self._log(f"   🔄 Retrying with corrections...")
                    
                    # Brief delay before retry
                    await asyncio.sleep(1)
                    continue
                
                else:
                    # Failed and no retry (max iterations for stage reached)
                    loop_state.status = LoopStatus.FAILED
                    loop_state.completed_at = datetime.utcnow()
                    loop_state.final_result = stage_output
                    loop_state.error_message = "Stage validation failed - no retry available"
                    loop_state.iteration_metrics.append(metrics)
                    
                    self._log(f"\n❌ FAILED: Stage '{stage_name}' validation failed")
                    self._log_validation_summary(validation_report)
                    
                    await self._log_to_supabase(loop_state, validation_report)
                    
                    return False, stage_output, loop_state
                    
            except Exception as e:
                # Execution error
                metrics.completed_at = datetime.utcnow()
                metrics.duration_seconds = (metrics.completed_at - metrics.started_at).total_seconds()
                loop_state.iteration_metrics.append(metrics)
                
                error_msg = f"Execution error on iteration {iteration}: {str(e)}"
                self._log(f"   ❌ ERROR: {error_msg}")
                
                if iteration < max_iter:
                    self._log(f"   🔄 Retrying after error...")
                    await asyncio.sleep(2)
                    continue
                else:
                    loop_state.status = LoopStatus.FAILED
                    loop_state.completed_at = datetime.utcnow()
                    loop_state.error_message = error_msg
                    
                    return False, loop_state.stage_output, loop_state
        
        # Max iterations reached without success
        loop_state.status = LoopStatus.MAX_ITERATIONS
        loop_state.completed_at = datetime.utcnow()
        loop_state.error_message = f"Max iterations ({max_iter}) reached without passing validation"
        
        self._log(f"\n⏱️  MAX ITERATIONS: Stopped after {max_iter} attempts")
        
        await self._log_to_supabase(loop_state, loop_state.validation_history[-1] if loop_state.validation_history else None)
        
        return False, loop_state.stage_output, loop_state
    
    async def _execute_with_router(
        self,
        executor: Callable,
        input_data: Dict[str, Any],
        iteration: int,
        stage_name: str,
        metrics: IterationMetrics
    ) -> Dict[str, Any]:
        """Execute stage logic with Smart Router integration"""
        
        # Determine Smart Router tier from criteria
        stage_criteria = self.criteria['stages'].get(stage_name, {})
        router_tier = stage_criteria.get('smart_router_tier', 'FREE')
        
        metrics.smart_router_tier = router_tier
        
        # Execute stage
        if asyncio.iscoroutinefunction(executor):
            result = await executor(input_data, iteration)
        else:
            result = executor(input_data, iteration)
        
        # Track metrics
        if self.smart_router:
            # Get actual usage from Smart Router if available
            # This is a placeholder - actual implementation would query router
            metrics.api_calls = result.get('_meta', {}).get('api_calls', 1)
            metrics.cost_estimate = result.get('_meta', {}).get('cost', 0.0)
        else:
            # Estimate based on tier
            metrics.api_calls = 1
            metrics.cost_estimate = 0.0 if router_tier == 'FREE' else 0.01
        
        return result
    
    def _prepare_retry_input(
        self,
        original_input: Dict[str, Any],
        failed_output: Dict[str, Any],
        validation_report: StageValidationReport
    ) -> Dict[str, Any]:
        """
        Prepare input for retry attempt with corrections based on validation failures.
        
        This extracts failed checks and adds them to input so executor can fix issues.
        """
        retry_input = original_input.copy()
        
        # Add retry metadata
        retry_input['_retry_metadata'] = {
            'iteration': validation_report.iteration_number + 1,
            'previous_output': failed_output,
            'failed_checks': [
                {
                    'check': v.check_name,
                    'message': v.message,
                    'severity': v.severity.value
                }
                for v in validation_report.validation_results
                if not v.passed and v.severity == ValidationSeverity.CRITICAL
            ],
            'retry_instructions': validation_report.retry_instructions
        }
        
        return retry_input
    
    def _log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(message)
    
    def _log_validation_summary(self, report: StageValidationReport):
        """Log validation report summary"""
        if not self.verbose:
            return
        
        summary = report.to_dict()['summary']
        print(f"      Total checks: {summary['total_checks']}")
        print(f"      Passed: {summary['passed']} | Failed: {summary['failed']}")
        
        if summary['critical_failures'] > 0:
            print(f"      ⚠️  Critical failures: {summary['critical_failures']}")
            
            # Show first 3 critical failures
            critical = [
                v for v in report.validation_results
                if not v.passed and v.severity == ValidationSeverity.CRITICAL
            ][:3]
            
            for v in critical:
                print(f"         - {v.check_name}: {v.message}")
    
    async def _log_to_supabase(
        self,
        loop_state: RalphLoopState,
        validation_report: Optional[StageValidationReport]
    ):
        """Log loop execution to Supabase insights table"""
        if not self.supabase:
            return
        
        try:
            log_entry = {
                'loop_id': loop_state.loop_id,
                'stage_name': loop_state.stage_name,
                'status': loop_state.status.value,
                'iterations': loop_state.current_iteration,
                'total_cost': loop_state.total_cost,
                'duration_seconds': (loop_state.completed_at - loop_state.started_at).total_seconds() if loop_state.completed_at and loop_state.started_at else 0,
                'validation_passed': validation_report.passed if validation_report else False,
                'error_message': loop_state.error_message,
                'metrics': json.dumps([m.to_dict() for m in loop_state.iteration_metrics]),
                'created_at': datetime.utcnow().isoformat()
            }
            
            await self.supabase.table('ralph_loop_logs').insert(log_entry).execute()
        except Exception as e:
            self._log(f"   ⚠️  Failed to log to Supabase: {e}")
    
    def generate_loop_report(self, loop_state: RalphLoopState) -> Dict[str, Any]:
        """Generate comprehensive report of loop execution"""
        
        validation_summary = {
            'total_validations': len(loop_state.validation_history),
            'passed': sum(1 for v in loop_state.validation_history if v.passed),
            'failed': sum(1 for v in loop_state.validation_history if not v.passed)
        }
        
        cost_summary = {
            'total_cost': sum(m.cost_estimate for m in loop_state.iteration_metrics),
            'total_api_calls': sum(m.api_calls for m in loop_state.iteration_metrics),
            'free_tier_calls': sum(
                m.api_calls for m in loop_state.iteration_metrics
                if m.smart_router_tier == 'FREE'
            ),
            'free_tier_percentage': (
                sum(m.api_calls for m in loop_state.iteration_metrics if m.smart_router_tier == 'FREE') /
                sum(m.api_calls for m in loop_state.iteration_metrics) * 100
            ) if loop_state.iteration_metrics else 0
        }
        
        return {
            'loop_state': loop_state.to_dict(),
            'validation_summary': validation_summary,
            'cost_summary': cost_summary,
            'iterations': [m.to_dict() for m in loop_state.iteration_metrics],
            'final_validation': loop_state.validation_history[-1].to_dict() if loop_state.validation_history else None,
            'generated_at': datetime.utcnow().isoformat(),
            'created_by': 'Ariel Shapira, Solo Founder - Everest Capital USA'
        }


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

async def execute_with_ralph(
    stage_name: str,
    stage_executor: Callable,
    input_data: Dict[str, Any],
    max_iterations: int = 30,
    criteria_path: str = "success_criteria.json"
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to execute a stage with Ralph pattern.
    
    Usage:
        async def my_stage_executor(input_data, iteration):
            # Stage logic here
            return {'output': 'data'}
        
        success, output, report = await execute_with_ralph(
            'lien_priority',
            my_stage_executor,
            {'case_number': '05-2024-CA-123456-XXXX-XX'},
            max_iterations=20
        )
        
        if success:
            print("Stage completed!")
        else:
            print(f"Failed: {report['loop_state']['error_message']}")
    """
    orchestrator = RalphOrchestrator(criteria_path=criteria_path)
    success, output, loop_state = await orchestrator.execute_stage_loop(
        stage_name,
        stage_executor,
        input_data,
        max_iterations
    )
    
    report = orchestrator.generate_loop_report(loop_state)
    
    return success, output, report


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Example: Lien Priority stage with Ralph loop
    
    async def lien_priority_executor(input_data: Dict, iteration: int) -> Dict[str, Any]:
        """Example stage executor"""
        print(f"   Executing lien priority analysis (iteration {iteration})...")
        await asyncio.sleep(2)  # Simulate processing
        
        # Simulate improvement on retry
        if iteration == 1:
            # First attempt - incomplete
            return {
                'priority_order': [],
                'plaintiff_type': 'UNKNOWN',
                'senior_mortgage_survives': False
            }
        else:
            # Retry - complete
            return {
                'priority_order': [
                    {'document_number': '2024-123456', 'priority': 1, 'type': 'mortgage'},
                    {'document_number': '2024-123457', 'priority': 2, 'type': 'lien'}
                ],
                'plaintiff_type': 'BANK',
                'senior_mortgage_survives': False,
                'lien_stack': [
                    {'position': 1, 'type': 'First Mortgage', 'amount': 250000},
                    {'position': 2, 'type': 'Second Mortgage', 'amount': 50000}
                ]
            }
    
    async def main():
        orchestrator = RalphOrchestrator()
        
        input_data = {
            'case_number': '05-2024-CA-123456-XXXX-XX',
            'plaintiff': 'WELLS FARGO BANK'
        }
        
        success, output, loop_state = await orchestrator.execute_stage_loop(
            'lien_priority',
            lien_priority_executor,
            input_data,
            max_iterations=10
        )
        
        report = orchestrator.generate_loop_report(loop_state)
        print("\n" + "="*60)
        print("RALPH LOOP REPORT")
        print("="*60)
        print(json.dumps(report, indent=2))
    
    asyncio.run(main())
