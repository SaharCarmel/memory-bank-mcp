"""
Architecture Agent - Phase 1 of Multi-Agent Memory Bank Builder

This agent analyzes a codebase to identify its architectural pattern and major components,
creating an architectural manifest that guides subsequent component agents.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import SystemMessage

logger = logging.getLogger(__name__)


class ArchitectureType(str, Enum):
    """Detected architecture patterns"""
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    MODULAR_MONOLITH = "modular_monolith"
    SERVERLESS = "serverless"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Types of components that can be identified"""
    SERVICE = "service"
    FRONTEND = "frontend"
    BACKEND = "backend"
    LIBRARY = "library"
    MODULE = "module"
    WORKER = "worker"
    API_GATEWAY = "api_gateway"
    DATABASE = "database"


@dataclass
class Component:
    """Represents a major component in the codebase"""
    name: str
    type: ComponentType
    path: str
    technology: str
    complexity: str  # low, medium, high
    dependencies: List[str]
    description: str
    entry_points: List[str] = None
    estimated_size: Dict[str, int] = None  # files, lines of code


@dataclass
class ArchitectureManifest:
    """The complete architectural analysis output"""
    system_type: ArchitectureType
    architecture_diagram: str  # Mermaid diagram
    components: List[Component]
    total_components: int
    estimated_parallel_agents: int
    breakdown_rationale: str
    analysis_metadata: Dict[str, Any]
    generated_at: str


class ArchitectureAgent:
    """Analyzes codebase structure to create architectural manifest"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the architecture agent"""
        return """<role>
You are an expert software architect analyzing a codebase to create a hierarchical memory bank system.
</role>

<context>
You are the first phase in a multi-agent system. Your analysis will determine how subsequent agents divide their work. The quality of your architectural breakdown directly impacts the entire system's effectiveness.
</context>

<task>
Analyze this codebase and create an architectural manifest that identifies major components for parallel analysis.
</task>

<instructions>
1. First, explore the repository structure using LS, Glob, and Read tools
2. Identify the architectural pattern (microservices, monolith, modular monolith, etc.)
3. Detect major components based on:
   - Service boundaries (separate deployable units)
   - Distinct applications (frontend, backend, workers)
   - Major functional modules
   - Shared libraries used across multiple components

4. For each component, determine:
   - Name and type (service/frontend/library/module)
   - Root path
   - Primary technology stack
   - Estimated complexity (lines of code, number of files)
   - Dependencies on other components

5. Create an architecture diagram using Mermaid syntax

6. Decide on appropriate breakdown depth:
   - Aim for 5-20 top-level components
   - Each component should be substantial enough to warrant its own memory bank
   - Avoid going too deep (e.g., don't create components for individual classes)
</instructions>

<output_format>
Create a file called `architecture_manifest.md` with this structure:

```markdown
# Architecture Analysis

## System Type
[Identified architecture pattern]

## Architecture Diagram
```mermaid
graph TD
    [Component relationships]
```

## Components

### Component: [name]
- **Type**: service|frontend|library|module
- **Path**: /path/to/component
- **Technology**: [primary stack]
- **Complexity**: low|medium|high
- **Dependencies**: [list of other components]
- **Description**: [brief description]

[Repeat for each component]

## Analysis Metadata
- Total Components: [number]
- Estimated Parallel Agents Needed: [number]
- Breakdown Rationale: [explanation of why you chose this level of granularity]
```
</output_format>

<thinking_process>
Before creating the manifest, use a <component_analysis> section to think through:
1. What is the overall structure?
2. What are the natural boundaries?
3. What level of breakdown makes sense?
4. How can I ensure good parallelization without too much overhead?
</thinking_process>"""

    async def analyze(
        self, 
        repo_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns: int = 200,
        cost_calculator: Optional['CostCalculator'] = None
    ) -> ArchitectureManifest:
        """
        Analyze the repository and create architectural manifest
        
        Args:
            repo_path: Path to the repository to analyze
            output_path: Where to save the manifest
            progress_callback: Optional callback for progress updates
            
        Returns:
            ArchitectureManifest object with analysis results
        """
        repo_path = Path(repo_path).resolve()
        output_path = Path(output_path).resolve()
        
        # Validate repository path
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
            
        await self._call_progress_callback(progress_callback, "Starting architectural analysis...")
        
        # Create the analysis prompt
        prompt = self._create_analysis_prompt(output_path)
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=max_turns,  # Configurable for large repositories
            system_prompt=self.system_prompt,
            cwd=str(repo_path),
            allowed_tools=["Read", "Glob", "LS", "Write", "Grep"],
            permission_mode="bypassPermissions",
        )
        
        await self._call_progress_callback(progress_callback, "Analyzing codebase structure...")
        
        manifest_created = False
        manifest_path = output_path / "architecture_manifest.md"
        turn_count = 0
        turn_warning_threshold = int(max_turns * 0.95)  # Warn at 95% of max turns
        
        try:
            # Stream messages from Claude Code
            async for message in query(prompt=prompt, options=options):
                turn_count += 1
                
                # Check if approaching turn limit
                if turn_count == turn_warning_threshold:
                    warning_msg = f"⚠️ WARNING: Approaching turn limit ({turn_count}/{max_turns}). Agent may not complete analysis!"
                    await self._call_progress_callback(progress_callback, warning_msg)
                    logger.warning(warning_msg)
                elif turn_count % 50 == 0:
                    await self._call_progress_callback(progress_callback, f"Progress: {turn_count} turns completed")
                # Handle different message types
                if hasattr(message, 'content'):
                    content = message.content
                    
                    if isinstance(content, list):
                        for block in content:
                            # Track tool usage
                            if hasattr(block, 'name') and hasattr(block, 'input'):
                                tool_name = block.name
                                tool_input = block.input
                                
                                if tool_name == "Write" and tool_input.get('file_path', '').endswith('architecture_manifest.md'):
                                    manifest_created = True
                                    await self._call_progress_callback(progress_callback, "Architecture manifest created")
                                elif tool_name == "LS":
                                    path = tool_input.get('path', 'current directory')
                                    await self._call_progress_callback(progress_callback, f"Exploring: {path}")
                                elif tool_name == "Read":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    await self._call_progress_callback(progress_callback, f"Analyzing: {file_path}")
                                elif tool_name == "Glob":
                                    pattern = tool_input.get('pattern', 'unknown')
                                    await self._call_progress_callback(progress_callback, f"Searching for: {pattern}")
            
            # Log final turn count
            await self._call_progress_callback(progress_callback, f"Analysis completed in {turn_count} turns")
            
            if turn_count >= max_turns:
                await self._call_progress_callback(
                    progress_callback, 
                    f"⚠️ REACHED MAX TURNS LIMIT ({max_turns})! Analysis may be incomplete."
                )
                logger.warning(f"Architecture analysis hit max turns limit of {max_turns}")
            
            if not manifest_created or not manifest_path.exists():
                if turn_count >= turn_warning_threshold:
                    raise RuntimeError(f"Architecture manifest was not created. Hit turn limit ({turn_count}/{max_turns})")
                else:
                    raise RuntimeError("Architecture manifest was not created")
                
            # Parse the created manifest
            await self._call_progress_callback(progress_callback, "Parsing architecture manifest...")
            manifest = self._parse_manifest(manifest_path)
            
            await self._call_progress_callback(progress_callback, f"Analysis complete: {manifest.total_components} components identified")
            
            # Save manifest as JSON for easier parsing by other agents
            json_path = output_path / "architecture_manifest.json"
            with open(json_path, 'w') as f:
                json.dump(asdict(manifest), f, indent=2)
            
            return manifest
            
        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            await self._call_progress_callback(progress_callback, f"Error: {e}")
            raise
    
    def _create_analysis_prompt(self, output_path: Path) -> str:
        """Create the prompt for architectural analysis"""
        return f"""Analyze this codebase thoroughly to understand its architecture and identify major components.

Your goal is to create an architectural manifest that will guide other agents in analyzing individual components.

Important guidelines:
1. Start by exploring the root directory structure efficiently
2. Look for key configuration files (setup.py, CMakeLists.txt, docker-compose.yml, package.json, etc.)
3. For large repositories like PyTorch:
   - Focus on top-level directories first
   - Don't dive too deep into individual files initially
   - Look for natural module boundaries (torch/, caffe2/, aten/, etc.)
   - Identify core vs auxiliary components
4. Create a clear Mermaid diagram showing component relationships
5. Write the manifest to: {output_path}/architecture_manifest.md

EFFICIENCY TIPS:
- Use Glob patterns to quickly identify structure (e.g., "*/setup.py", "*/CMakeLists.txt")
- Read only key files that help identify architecture
- Don't analyze individual source files unless necessary
- Aim for 10-20 major components for large codebases

Begin your analysis now."""

    def _parse_manifest(self, manifest_path: Path) -> ArchitectureManifest:
        """Parse the markdown manifest into structured data"""
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        # This is a simplified parser - in production, we'd use a proper markdown parser
        # For now, we'll extract key information using string operations
        
        components = []
        system_type = ArchitectureType.UNKNOWN
        architecture_diagram = ""
        
        # Extract system type
        if "microservices" in content.lower():
            system_type = ArchitectureType.MICROSERVICES
        elif "monolith" in content.lower() and "modular" in content.lower():
            system_type = ArchitectureType.MODULAR_MONOLITH
        elif "monolith" in content.lower():
            system_type = ArchitectureType.MONOLITH
        elif "serverless" in content.lower():
            system_type = ArchitectureType.SERVERLESS
        
        # Extract diagram (between ```mermaid and ```)
        import re
        diagram_match = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
        if diagram_match:
            architecture_diagram = diagram_match.group(1)
        
        # Extract components (simplified - looks for ### Component: patterns)
        component_matches = re.findall(r'### Component: (.*?)\n(.*?)(?=###|$)', content, re.DOTALL)
        
        for name, details in component_matches:
            component_data = {
                'name': name.strip(),
                'type': ComponentType.SERVICE,  # Default
                'path': '/',
                'technology': 'unknown',
                'complexity': 'medium',
                'dependencies': [],
                'description': ''
            }
            
            # Extract component details
            for line in details.split('\n'):
                if '**Type**:' in line:
                    type_str = line.split(':', 1)[1].strip()
                    try:
                        component_data['type'] = ComponentType(type_str)
                    except:
                        pass
                elif '**Path**:' in line:
                    component_data['path'] = line.split(':', 1)[1].strip()
                elif '**Technology**:' in line:
                    component_data['technology'] = line.split(':', 1)[1].strip()
                elif '**Complexity**:' in line:
                    component_data['complexity'] = line.split(':', 1)[1].strip()
                elif '**Dependencies**:' in line:
                    deps_str = line.split(':', 1)[1].strip()
                    component_data['dependencies'] = [d.strip() for d in deps_str.split(',') if d.strip()]
                elif '**Description**:' in line:
                    component_data['description'] = line.split(':', 1)[1].strip()
            
            components.append(Component(**component_data))
        
        # Create manifest
        return ArchitectureManifest(
            system_type=system_type,
            architecture_diagram=architecture_diagram,
            components=components,
            total_components=len(components),
            estimated_parallel_agents=min(len(components), 10),  # Cap at 10 concurrent
            breakdown_rationale="Components identified based on service boundaries and logical modules",
            analysis_metadata={
                "analyzer_version": "1.0.0",
                "analysis_duration": "unknown"
            },
            generated_at=datetime.now().isoformat()
        )
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)