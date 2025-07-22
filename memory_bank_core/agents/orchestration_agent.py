"""
Orchestration Agent - Manages parallel execution of Component Agents

This agent coordinates the parallel execution of component agents based on the
architectural manifest from Phase 1.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .architecture_agent import ArchitectureManifest, Component
from .component_agent import ComponentAgent, ComponentAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result of orchestrated component analysis"""
    total_components: int
    successful_components: int
    failed_components: int
    component_results: List[ComponentAnalysisResult]
    orchestration_metadata: Dict[str, Any]
    total_duration_seconds: float


class OrchestrationAgent:
    """Orchestrates parallel execution of component agents"""
    
    def __init__(self, root_path: Path, max_concurrent_agents: int = 5):
        self.root_path = Path(root_path)
        self.max_concurrent_agents = max_concurrent_agents
        
    async def orchestrate_component_analysis(
        self,
        manifest: ArchitectureManifest,
        repo_path: str,
        output_base_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns_per_component: int = 150
    ) -> OrchestrationResult:
        """
        Orchestrate parallel analysis of all components
        
        Args:
            manifest: Architecture manifest from Phase 1
            repo_path: Path to the repository
            output_base_path: Base path for output
            progress_callback: Optional callback for progress updates
            max_turns_per_component: Max turns per component agent
            
        Returns:
            OrchestrationResult with aggregated results
        """
        start_time = datetime.now()
        
        await self._call_progress_callback(
            progress_callback,
            f"=== PHASE 2: Component Analysis ({len(manifest.components)} components) ==="
        )
        
        await self._call_progress_callback(
            progress_callback,
            f"Max concurrent agents: {self.max_concurrent_agents}"
        )
        
        # Create architecture summary for component agents
        architecture_summary = self._create_architecture_summary(manifest)
        
        # Create semaphore to limit concurrent agents
        semaphore = asyncio.Semaphore(self.max_concurrent_agents)
        
        # Create tasks for all components
        tasks = []
        for component in manifest.components:
            task = asyncio.create_task(
                self._analyze_component_with_semaphore(
                    semaphore=semaphore,
                    component=component,
                    repo_path=repo_path,
                    output_base_path=output_base_path,
                    architecture_summary=architecture_summary,
                    progress_callback=progress_callback,
                    max_turns=max_turns_per_component
                )
            )
            tasks.append(task)
        
        # Wait for all components to complete
        await self._call_progress_callback(
            progress_callback,
            f"Starting analysis of {len(tasks)} components..."
        )
        
        component_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(component_results):
            if isinstance(result, Exception):
                # Create a failed result for the exception
                component_name = manifest.components[i].name if i < len(manifest.components) else f"component_{i}"
                failed_result = ComponentAnalysisResult(
                    component_name=component_name,
                    success=False,
                    output_path="",
                    files_written=[],
                    analysis_metadata={},
                    errors=[str(result)]
                )
                failed_results.append(failed_result)
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component_name}] ❌ Failed with exception: {result}"
                )
            else:
                if result.success:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log final results
        await self._call_progress_callback(
            progress_callback,
            f"Component analysis completed in {duration:.2f} seconds"
        )
        await self._call_progress_callback(
            progress_callback,
            f"✅ Successful: {len(successful_results)}, ❌ Failed: {len(failed_results)}"
        )
        
        # Create aggregated result
        all_results = successful_results + failed_results
        
        orchestration_result = OrchestrationResult(
            total_components=len(manifest.components),
            successful_components=len(successful_results),
            failed_components=len(failed_results),
            component_results=all_results,
            orchestration_metadata={
                "max_concurrent_agents": self.max_concurrent_agents,
                "max_turns_per_component": max_turns_per_component,
                "architecture_type": manifest.system_type,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "parallel_execution": True
            },
            total_duration_seconds=duration
        )
        
        # Save orchestration summary
        await self._save_orchestration_summary(orchestration_result, output_base_path)
        
        return orchestration_result
    
    async def _analyze_component_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        component: Component,
        repo_path: str,
        output_base_path: str,
        architecture_summary: str,
        progress_callback: Optional[Callable],
        max_turns: int
    ) -> ComponentAnalysisResult:
        """Analyze a component with semaphore control"""
        async with semaphore:
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] Starting analysis (agent acquired)"
            )
            
            component_agent = ComponentAgent(self.root_path)
            
            try:
                result = await component_agent.analyze_component(
                    component=component,
                    repo_path=repo_path,
                    output_base_path=output_base_path,
                    architecture_summary=architecture_summary,
                    progress_callback=progress_callback,
                    max_turns=max_turns
                )
                
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] {'✅ Completed' if result.success else '⚠️ Partially completed'} (agent released)"
                )
                
                return result
                
            except Exception as e:
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ❌ Failed: {e} (agent released)"
                )
                raise e
    
    def _create_architecture_summary(self, manifest: ArchitectureManifest) -> str:
        """Create a summary of the architecture for component agents"""
        component_list = "\n".join([
            f"- {comp.name} ({comp.type}): {comp.path}"
            for comp in manifest.components
        ])
        
        return f"""System Type: {manifest.system_type}

Components:
{component_list}

Architecture Diagram:
{manifest.architecture_diagram}

Total Components: {manifest.total_components}"""
    
    async def _save_orchestration_summary(self, result: OrchestrationResult, output_base_path: str):
        """Save orchestration summary to file"""
        output_path = Path(output_base_path)
        summary_path = output_path / "component_analysis_summary.json"
        
        # Create summary data
        summary_data = {
            "total_components": result.total_components,
            "successful_components": result.successful_components,
            "failed_components": result.failed_components,
            "success_rate": result.successful_components / result.total_components if result.total_components > 0 else 0,
            "total_duration_seconds": result.total_duration_seconds,
            "orchestration_metadata": result.orchestration_metadata,
            "component_summaries": []
        }
        
        # Add component summaries
        for comp_result in result.component_results:
            comp_summary = {
                "component_name": comp_result.component_name,
                "success": comp_result.success,
                "output_path": comp_result.output_path,
                "files_created": len(comp_result.files_written),
                "turn_count": comp_result.analysis_metadata.get("turn_count", 0),
                "created_files": comp_result.analysis_metadata.get("created_files", []),
                "missing_files": comp_result.analysis_metadata.get("missing_files", []),
                "errors": comp_result.errors or []
            }
            summary_data["component_summaries"].append(comp_summary)
        
        # Write summary
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Orchestration summary saved to: {summary_path}")
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)