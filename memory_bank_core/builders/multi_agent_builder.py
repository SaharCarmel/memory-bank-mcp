"""
Multi-Agent Memory Bank Builder

This builder implements the multi-phase agent system:
- Phase 1: Architecture Analysis
- Phase 2: Component Analysis (parallel)
- Phase 3: Validation & Auto-fix (parallel)
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from ..models.build_job import BuildConfig, BuildResult, BuildMode
from ..agents.architecture_agent import ArchitectureAgent, ArchitectureManifest
from ..agents.orchestration_agent import OrchestrationAgent, OrchestrationResult
from ..agents.validation_orchestrator import ValidationOrchestrator, ValidationOrchestrationResult
from ..exceptions.build import BuildError

logger = logging.getLogger(__name__)


class MultiAgentMemoryBankBuilder:
    """Orchestrates multi-agent memory bank building"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        
    async def build_memory_bank(
        self,
        config: BuildConfig,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> BuildResult:
        """
        Build memory bank using multi-agent system
        
        Args:
            config: Build configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            BuildResult with build results
        """
        repo_path = Path(config.repo_path).resolve()
        output_path = Path(config.output_path).resolve()
        
        # Validate repository path
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
            
        # Create output directories
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Phase 1: Architecture Analysis
            await self._call_progress_callback(progress_callback, "=== PHASE 1: Architecture Analysis ===")
            
            architecture_agent = ArchitectureAgent(self.root_path)
            
            # Pass max_turns from config if available
            if hasattr(config, 'max_turns'):
                await self._call_progress_callback(
                    progress_callback, 
                    f"Using max_turns: {config.max_turns} for architecture analysis"
                )
            
            manifest = await architecture_agent.analyze(
                repo_path=str(repo_path),
                output_path=str(output_path),
                progress_callback=progress_callback,
                max_turns=config.max_turns if hasattr(config, 'max_turns') else 200
            )
            
            await self._call_progress_callback(
                progress_callback, 
                f"Architecture analysis complete: {manifest.total_components} components identified"
            )
            
            # Log manifest summary
            await self._call_progress_callback(progress_callback, f"System Type: {manifest.system_type}")
            await self._call_progress_callback(progress_callback, f"Components breakdown:")
            for component in manifest.components:
                await self._call_progress_callback(
                    progress_callback,
                    f"  - {component.name} ({component.type}): {component.path}"
                )
            
            # Phase 2: Component Analysis (if components exist)
            files_written = [
                str(output_path / "architecture_manifest.md"),
                str(output_path / "architecture_manifest.json")
            ]
            
            orchestration_result = None
            
            if manifest.components and len(manifest.components) > 0:
                await self._call_progress_callback(progress_callback, "=== PHASE 2: Component Analysis ===")
                
                orchestration_agent = OrchestrationAgent(
                    root_path=self.root_path,
                    max_concurrent_agents=min(15, len(manifest.components))  # Hard limit of 15 agents
                )
                
                orchestration_result = await orchestration_agent.orchestrate_component_analysis(
                    manifest=manifest,
                    repo_path=str(repo_path),
                    output_base_path=str(output_path),
                    progress_callback=progress_callback,
                    max_turns_per_component=config.max_turns // 2 if hasattr(config, 'max_turns') else 75
                )
                
                # Add component analysis files to files_written
                for comp_result in orchestration_result.component_results:
                    files_written.extend(comp_result.files_written)
                
                # Add orchestration summary
                files_written.append(str(output_path / "component_analysis_summary.json"))
                
                await self._call_progress_callback(
                    progress_callback,
                    f"Phase 2 complete: {orchestration_result.successful_components}/{orchestration_result.total_components} components analyzed successfully"
                )
            else:
                await self._call_progress_callback(progress_callback, "No components identified - skipping Phase 2")
            
            # Phase 3: Validation & Auto-Fix (if Phase 2 completed successfully)
            validation_result = None
            
            if orchestration_result and orchestration_result.successful_components > 0:
                await self._call_progress_callback(progress_callback, "=== PHASE 3: Validation & Auto-Fix ===")
                
                validation_orchestrator = ValidationOrchestrator(
                    root_path=self.root_path,
                    max_concurrent_validators=min(10, orchestration_result.successful_components)
                )
                
                validation_result = await validation_orchestrator.orchestrate_validation(
                    manifest=manifest,
                    orchestration_result=orchestration_result,
                    repo_path=str(repo_path),
                    output_base_path=str(output_path),
                    progress_callback=progress_callback,
                    max_turns_per_validator=config.max_turns // 4 if hasattr(config, 'max_turns') else 50
                )
                
                # Add validation summary to files_written
                files_written.append(str(output_path / "validation_summary.json"))
                
                await self._call_progress_callback(
                    progress_callback,
                    f"Phase 3 complete: {validation_result.components_passed} passed, {validation_result.total_issues_fixed} issues fixed"
                )
            else:
                await self._call_progress_callback(progress_callback, "No successful components - skipping Phase 3")
            
            # Build metadata
            metadata = {
                "mode": "multi_agent",
                "phase_1_complete": True,
                "phase_2_complete": orchestration_result is not None,
                "phase_3_complete": validation_result is not None,
                "architecture_type": manifest.system_type,
                "total_components": manifest.total_components,
                "components": [c.name for c in manifest.components],
                "generated_at": datetime.now().isoformat()
            }
            
            if orchestration_result:
                metadata.update({
                    "successful_components": orchestration_result.successful_components,
                    "failed_components": orchestration_result.failed_components,
                    "component_analysis_duration": orchestration_result.total_duration_seconds
                })
            
            if validation_result:
                metadata.update({
                    "validation_passed": validation_result.components_passed,
                    "validation_failed": validation_result.components_failed,
                    "validation_partial": validation_result.components_partial,
                    "total_issues_found": validation_result.total_issues_found,
                    "total_issues_fixed": validation_result.total_issues_fixed,
                    "validation_duration": validation_result.total_duration_seconds,
                    "fix_success_rate": validation_result.total_issues_fixed / validation_result.total_issues_found if validation_result.total_issues_found > 0 else 0
                })
            
            return BuildResult(
                success=True,
                output_path=str(output_path),
                files_written=files_written,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Multi-agent build failed: {e}")
            await self._call_progress_callback(progress_callback, f"Error: {e}")
            
            return BuildResult(
                success=False,
                output_path=str(output_path),
                files_written=[],
                metadata={},
                errors=[str(e)]
            )
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)