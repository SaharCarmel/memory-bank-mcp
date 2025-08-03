"""
Component Agent - Phase 2 of Multi-Agent Memory Bank Builder

This agent analyzes individual components in detail, creating focused memory banks
for each component identified by the Architecture Agent.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import asyncio
from dataclasses import dataclass

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import SystemMessage

from .architecture_agent import Component, ComponentType

logger = logging.getLogger(__name__)


@dataclass
class ComponentAnalysisResult:
    """Result of component analysis"""
    component_name: str
    success: bool
    output_path: str
    files_written: List[str]
    analysis_metadata: Dict[str, Any]
    errors: List[str] = None


class ComponentAgent:
    """Analyzes individual components to create focused memory banks"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        
    def _create_component_system_prompt(self, component: Component, architecture_summary: str) -> str:
        """Create system prompt for component analysis"""
        return f"""<role>
You are a specialized code analyst focusing on a specific component within a larger system.
</role>

<context>
You are analyzing the component: {component.name}
Component Type: {component.type}
Component Path: {component.path}

This component is part of a larger system with architecture:
{architecture_summary}
</context>

<task>
Create a comprehensive memory bank for this specific component, focusing on its internal structure, patterns, and implementation details.
</task>

<constraints>
- Stay within the scope of your assigned component: {component.path}
- Reference but don't analyze external dependencies in detail
- Focus on implementation specifics rather than system-wide concerns
- Be thorough but stay focused on this component only
</constraints>

<memory_bank_sections>
Create these files in the component's memory-bank directory:

1. **projectbrief.md**: Component-specific purpose and goals
2. **techContext.md**: Technologies, frameworks, internal dependencies
3. **systemPatterns.md**: Design patterns, code organization within component
4. **activeContext.md**: Current state, recent changes, TODOs
5. **progress.md**: Implementation status, test coverage, known issues
6. **api_contracts.md**: Exposed APIs, interfaces, contracts (if applicable)
</memory_bank_sections>

<quality_guidelines>
- Be specific and concrete - cite actual files and line numbers
- Include code examples for key patterns
- Document actual behavior, not intended behavior
- Flag any inconsistencies or technical debt
- Focus on this component's internal architecture
</quality_guidelines>

<analysis_approach>
1. First, explore the component's directory structure
2. Identify the main entry points and core modules
3. Understand the component's public interfaces
4. Document internal architecture and patterns
5. Note dependencies and integration points
6. Identify areas for improvement or technical debt
</analysis_approach>"""

    def _create_component_analysis_prompt(self, component: Component, output_path: Path) -> str:
        """Create the analysis prompt for a specific component"""
        return f"""Analyze the component "{component.name}" located at {component.path}.

Your goal is to create a focused memory bank that captures:
1. The component's purpose and responsibilities
2. Its internal architecture and organization  
3. Key patterns and implementation details
4. Current state and development status
5. APIs and interfaces it exposes
6. Dependencies and integration points

Component Details:
- Name: {component.name}
- Type: {component.type}
- Path: {component.path}
- Technology: {component.technology}
- Complexity: {component.complexity}
- Description: {component.description}

Create the memory bank in: {output_path}

Important guidelines:
- Focus ONLY on files within {component.path}
- Don't analyze dependencies outside this component in detail
- Be thorough but stay scoped to this component
- Create all 6 required memory bank files
- Use concrete examples from the actual code

Begin your analysis now."""

    async def analyze_component(
        self,
        component: Component,
        repo_path: str,
        output_base_path: str,
        architecture_summary: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns: int = 150
    ) -> ComponentAnalysisResult:
        """
        Analyze a single component and create its memory bank
        
        Args:
            component: Component to analyze
            repo_path: Root path of the repository
            output_base_path: Base path for all memory banks
            architecture_summary: Summary of overall architecture
            progress_callback: Optional callback for progress updates
            max_turns: Maximum turns for Claude analysis
            
        Returns:
            ComponentAnalysisResult with analysis results
        """
        repo_path = Path(repo_path).resolve()
        component_output_path = Path(output_base_path) / "components" / component.name / "memory-bank"
        component_output_path.mkdir(parents=True, exist_ok=True)
        
        await self._call_progress_callback(
            progress_callback, 
            f"[{component.name}] Starting component analysis..."
        )
        
        # Create system prompt and analysis prompt
        system_prompt = self._create_component_system_prompt(component, architecture_summary)
        analysis_prompt = self._create_component_analysis_prompt(component, component_output_path)
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=["Read", "Glob", "LS", "Write", "Grep"],
            permission_mode="bypassPermissions",
        )
        
        files_written = []
        turn_count = 0
        turn_warning_threshold = int(max_turns * 0.9)  # Warn at 90% for components
        expected_files = [
            "projectbrief.md",
            "techContext.md", 
            "systemPatterns.md",
            "activeContext.md",
            "progress.md",
            "api_contracts.md"
        ]
        
        try:
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] Analyzing component structure..."
            )
            
            # Stream messages from Claude Code
            async for message in query(prompt=analysis_prompt, options=options):
                turn_count += 1
                
                # Check if approaching turn limit
                if turn_count == turn_warning_threshold:
                    warning_msg = f"[{component.name}] ⚠️ WARNING: Approaching turn limit ({turn_count}/{max_turns})"
                    await self._call_progress_callback(progress_callback, warning_msg)
                    logger.warning(warning_msg)
                elif turn_count % 25 == 0:
                    await self._call_progress_callback(
                        progress_callback, 
                        f"[{component.name}] Progress: {turn_count} turns"
                    )
                
                # Handle different message types
                if hasattr(message, 'content'):
                    content = message.content
                    
                    if isinstance(content, list):
                        for block in content:
                            # Track tool usage
                            if hasattr(block, 'name') and hasattr(block, 'input'):
                                tool_name = block.name
                                tool_input = block.input
                                
                                if tool_name == "Write":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    if file_path.endswith('.md'):
                                        files_written.append(file_path)
                                        filename = Path(file_path).name
                                        await self._call_progress_callback(
                                            progress_callback,
                                            f"[{component.name}] Created: {filename}"
                                        )
            
            # Log completion
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] Analysis completed in {turn_count} turns"
            )
            
            if turn_count >= max_turns:
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ⚠️ REACHED MAX TURNS LIMIT ({max_turns})!"
                )
            
            # Check which expected files were created
            created_files = []
            missing_files = []
            
            for expected_file in expected_files:
                file_path = component_output_path / expected_file
                if file_path.exists() and file_path.stat().st_size > 100:  # At least 100 bytes
                    created_files.append(expected_file)
                else:
                    missing_files.append(expected_file)
            
            success = len(missing_files) == 0
            
            if missing_files:
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ⚠️ Missing files: {', '.join(missing_files)}"
                )
            
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] ✅ Component analysis {'completed' if success else 'partially completed'}"
            )
            
            return ComponentAnalysisResult(
                component_name=component.name,
                success=success,
                output_path=str(component_output_path),
                files_written=files_written,
                analysis_metadata={
                    "turn_count": turn_count,
                    "max_turns": max_turns,
                    "created_files": created_files,
                    "missing_files": missing_files,
                    "component_type": component.type,
                    "component_path": component.path,
                    "completed_at": datetime.now().isoformat()
                },
                errors=missing_files if missing_files else []
            )
            
        except Exception as e:
            error_msg = f"Component analysis failed: {e}"
            logger.error(f"[{component.name}] {error_msg}")
            await self._call_progress_callback(progress_callback, f"[{component.name}] ❌ {error_msg}")
            
            return ComponentAnalysisResult(
                component_name=component.name,
                success=False,
                output_path=str(component_output_path),
                files_written=[],
                analysis_metadata={
                    "turn_count": turn_count,
                    "max_turns": max_turns,
                    "error_at_turn": turn_count
                },
                errors=[str(e)]
            )
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)