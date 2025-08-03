"""
Validation Orchestrator - Manages parallel validation and auto-fix of component memory banks

This orchestrator coordinates validation agents to ensure quality across all components.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .architecture_agent import ArchitectureManifest, Component
from .component_agent import ComponentAnalysisResult
from .validation_agent import ValidationAgent, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationOrchestrationResult:
    """Result of orchestrated validation and fixes"""
    total_components: int
    components_passed: int
    components_failed: int  
    components_partial: int
    total_issues_found: int
    total_issues_fixed: int
    validation_results: List[ValidationResult]
    orchestration_metadata: Dict[str, Any]
    total_duration_seconds: float


class ValidationOrchestrator:
    """Orchestrates parallel validation and auto-fix of component memory banks"""
    
    def __init__(self, root_path: Path, max_concurrent_validators: int = 10):
        self.root_path = Path(root_path)
        # Limit concurrent validators (less than component agents since validation is lighter)
        self.max_concurrent_validators = min(max_concurrent_validators, 10)
    
    async def orchestrate_validation(
        self,
        manifest: ArchitectureManifest,
        orchestration_result: 'OrchestrationResult',
        repo_path: str,
        output_base_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns_per_validator: int = 100
    ) -> ValidationOrchestrationResult:
        """
        Orchestrate parallel validation and auto-fix of all component memory banks
        
        Args:
            manifest: Architecture manifest from Phase 1
            orchestration_result: Results from Phase 2 component analysis
            repo_path: Path to the repository
            output_base_path: Base path for output
            progress_callback: Optional callback for progress updates
            max_turns_per_validator: Max turns per validation agent
            
        Returns:
            ValidationOrchestrationResult with aggregated results
        """
        start_time = datetime.now()
        
        await self._call_progress_callback(
            progress_callback,
            f"=== PHASE 3: Validation & Auto-Fix ({len(manifest.components)} components) ==="
        )
        
        await self._call_progress_callback(
            progress_callback,
            f"Max concurrent validators: {self.max_concurrent_validators}"
        )
        
        # Only validate components that were successfully analyzed in Phase 2
        successful_components = []
        for comp_result in orchestration_result.component_results:
            if comp_result.success:
                # Find corresponding component from manifest
                component = next(
                    (comp for comp in manifest.components if comp.name == comp_result.component_name),
                    None
                )
                if component:
                    successful_components.append((component, comp_result))
        
        if not successful_components:
            await self._call_progress_callback(
                progress_callback,
                "No successful components to validate - skipping Phase 3"
            )
            
            return ValidationOrchestrationResult(
                total_components=0,
                components_passed=0,
                components_failed=0,
                components_partial=0,
                total_issues_found=0,
                total_issues_fixed=0,
                validation_results=[],
                orchestration_metadata={
                    "reason": "no_successful_components",
                    "max_concurrent_validators": self.max_concurrent_validators
                },
                total_duration_seconds=0.0
            )
        
        await self._call_progress_callback(
            progress_callback,
            f"Validating {len(successful_components)} successfully analyzed components"
        )
        
        # Create semaphore to limit concurrent validators
        semaphore = asyncio.Semaphore(self.max_concurrent_validators)
        
        # Create validation tasks
        tasks = []
        for component, comp_result in successful_components:
            memory_bank_path = Path(comp_result.output_path)
            
            task = asyncio.create_task(
                self._validate_component_with_semaphore(
                    semaphore=semaphore,
                    component=component,
                    memory_bank_path=memory_bank_path,
                    repo_path=repo_path,
                    progress_callback=progress_callback,
                    max_turns=max_turns_per_validator
                )
            )
            tasks.append(task)
        
        # Wait for all validations to complete
        await self._call_progress_callback(
            progress_callback,
            f"Starting validation of {len(tasks)} components..."
        )
        
        validation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        successful_validations = []
        failed_validations = []
        
        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                # Create a failed result for the exception
                component_name = successful_components[i][0].name if i < len(successful_components) else f"component_{i}"
                failed_result = ValidationResult(
                    component_name=component_name,
                    validation_timestamp=datetime.now().isoformat(),
                    overall_status="FAIL",
                    completeness_score=0,
                    accuracy_score=0,
                    issues_found=[],
                    issues_fixed=[],
                    verified_claims=[],
                    fixes_applied=0,
                    validation_metadata={"error": str(result)}
                )
                failed_validations.append(failed_result)
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component_name}] ❌ Validation failed with exception: {result}"
                )
            else:
                successful_validations.append(result)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Aggregate statistics
        all_results = successful_validations + failed_validations
        components_passed = len([r for r in all_results if r.overall_status == "PASS"])
        components_partial = len([r for r in all_results if r.overall_status == "PARTIAL"])
        components_failed = len([r for r in all_results if r.overall_status == "FAIL"])
        
        total_issues_found = sum(len(r.issues_found) for r in all_results)
        total_issues_fixed = sum(r.fixes_applied for r in all_results)
        
        # Log final results
        await self._call_progress_callback(
            progress_callback,
            f"Validation completed in {duration:.2f} seconds"
        )
        await self._call_progress_callback(
            progress_callback,
            f"✅ Passed: {components_passed}, ⚠️ Partial: {components_partial}, ❌ Failed: {components_failed}"
        )
        await self._call_progress_callback(
            progress_callback,
            f"🔧 Total fixes applied: {total_issues_fixed} (from {total_issues_found} issues found)"
        )
        
        # Create orchestration result
        validation_orchestration_result = ValidationOrchestrationResult(
            total_components=len(all_results),
            components_passed=components_passed,
            components_failed=components_failed,
            components_partial=components_partial,
            total_issues_found=total_issues_found,
            total_issues_fixed=total_issues_fixed,
            validation_results=all_results,
            orchestration_metadata={
                "max_concurrent_validators": self.max_concurrent_validators,
                "max_turns_per_validator": max_turns_per_validator,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "validation_success_rate": components_passed / len(all_results) if all_results else 0,
                "fix_success_rate": total_issues_fixed / total_issues_found if total_issues_found > 0 else 0
            },
            total_duration_seconds=duration
        )
        
        # Save validation summary
        await self._save_validation_summary(validation_orchestration_result, output_base_path)
        
        return validation_orchestration_result
    
    async def _validate_component_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        component: Component,
        memory_bank_path: Path,
        repo_path: str,
        progress_callback: Optional[Callable],
        max_turns: int
    ) -> ValidationResult:
        """Validate a component with semaphore control"""
        async with semaphore:
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] 🔍 Starting validation (validator acquired)"
            )
            
            validation_agent = ValidationAgent(self.root_path)
            
            try:
                result = await validation_agent.validate_and_fix_component(
                    component=component,
                    memory_bank_path=memory_bank_path,
                    repo_path=repo_path,
                    progress_callback=progress_callback,
                    max_turns=max_turns
                )
                
                status_emoji = "✅" if result.overall_status == "PASS" else "⚠️" if result.overall_status == "PARTIAL" else "❌"
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] {status_emoji} Validation {result.overall_status.lower()} - {result.fixes_applied} fixes applied (validator released)"
                )
                
                return result
                
            except Exception as e:
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ❌ Validation failed: {e} (validator released)"
                )
                raise e
    
    async def _save_validation_summary(self, result: ValidationOrchestrationResult, output_base_path: str):
        """Save validation orchestration summary to file"""
        output_path = Path(output_base_path)
        summary_path = output_path / "validation_summary.json"
        
        # Create summary data
        summary_data = {
            "total_components": result.total_components,
            "components_passed": result.components_passed,
            "components_failed": result.components_failed,
            "components_partial": result.components_partial,
            "pass_rate": result.components_passed / result.total_components if result.total_components > 0 else 0,
            "total_issues_found": result.total_issues_found,
            "total_issues_fixed": result.total_issues_fixed,
            "fix_success_rate": result.total_issues_fixed / result.total_issues_found if result.total_issues_found > 0 else 0,
            "total_duration_seconds": result.total_duration_seconds,
            "orchestration_metadata": result.orchestration_metadata,
            "component_validation_summaries": []
        }
        
        # Add component validation summaries
        for validation_result in result.validation_results:
            comp_summary = {
                "component_name": validation_result.component_name,
                "overall_status": validation_result.overall_status,
                "completeness_score": validation_result.completeness_score,
                "accuracy_score": validation_result.accuracy_score,
                "issues_found": len(validation_result.issues_found),
                "issues_fixed": validation_result.fixes_applied,
                "verified_claims": len(validation_result.verified_claims),
                "turn_count": validation_result.validation_metadata.get("turn_count", 0)
            }
            summary_data["component_validation_summaries"].append(comp_summary)
        
        # Write summary
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Validation summary saved to: {summary_path}")
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)