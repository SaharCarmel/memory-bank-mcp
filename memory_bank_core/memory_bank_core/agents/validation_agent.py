"""
Validation Agent - Phase 3 of Multi-Agent Memory Bank Builder

This agent validates memory bank content for accuracy and completeness,
and automatically fixes issues found during validation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import asyncio
from dataclasses import dataclass
from enum import Enum

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk.types import SystemMessage

from .architecture_agent import Component
from .component_agent import ComponentAnalysisResult

logger = logging.getLogger(__name__)


class IssueType(str, Enum):
    """Types of issues that can be found"""
    MISSING = "missing"
    INACCURATE = "inaccurate" 
    INCONSISTENT = "inconsistent"
    EMPTY = "empty"
    INCOMPLETE = "incomplete"


class IssueSeverity(str, Enum):
    """Severity levels for issues"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ValidationIssue:
    """Represents a validation issue found"""
    severity: IssueSeverity
    issue_type: IssueType
    file: str
    description: str
    evidence: str
    suggestion: str
    auto_fixable: bool = False


@dataclass
class VerifiedClaim:
    """Represents a verified claim from memory bank"""
    claim: str
    source_file: str
    line_numbers: str
    verification_status: str  # VERIFIED, FAILED, PARTIAL


@dataclass
class ValidationResult:
    """Result of validation with auto-fix"""
    component_name: str
    validation_timestamp: str
    overall_status: str  # PASS, FAIL, PARTIAL
    completeness_score: int  # 0-100
    accuracy_score: int  # 0-100
    issues_found: List[ValidationIssue]
    issues_fixed: List[ValidationIssue]
    verified_claims: List[VerifiedClaim]
    fixes_applied: int
    validation_metadata: Dict[str, Any]


class ValidationAgent:
    """Validates and fixes memory bank content"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        
    def _create_validation_system_prompt(self, component: Component) -> str:
        """Create system prompt for validation agent"""
        return f"""<role>
You are a quality assurance specialist validating memory bank content for accuracy and completeness.
</role>

<context>
Component being validated: {component.name}
Memory bank path: components/{component.name}/memory-bank/
Source code path: {component.path}
</context>

<task>
Validate that the memory bank accurately represents the codebase and meets quality standards. 
After validation, automatically fix any issues you can resolve.
</task>

<validation_checklist>
## 1. Completeness Validation
- [ ] All required files exist (projectbrief.md, techContext.md, etc.)
- [ ] Each file has substantial content (>500 characters)
- [ ] No placeholder text ("TODO", "TBD", "[Add content here]")
- [ ] All sections in each file are populated

## 2. Accuracy Validation
- [ ] Verify 5 random technical claims by checking source code
- [ ] Validate file paths mentioned actually exist
- [ ] Check that described APIs match implementation
- [ ] Verify dependency lists are accurate

## 3. Consistency Validation
- [ ] Component description aligns with parent architecture
- [ ] No contradictions between different files
- [ ] Technical stack matches actual usage

## 4. Code Evidence
For each major claim, find and verify:
- Specific file and line number
- Actual code snippet
- Confirmation that description matches implementation
</validation_checklist>

<auto_fix_capabilities>
You can automatically fix these types of issues:
1. Missing files - create with appropriate content
2. Empty sections - populate with analyzed content  
3. Placeholder text - replace with actual information
4. Inconsistent information - correct based on source code
5. Missing dependencies - add after verification
6. Broken file paths - correct to actual paths
</auto_fix_capabilities>

<output_format>
First, perform validation and identify issues.
Then, automatically fix issues you can resolve.
Finally, create `validation_report.json` with results.
</output_format>

<reasoning_approach>
Use <validation_thinking> tags to work through each check:
1. What is claimed in the memory bank?
2. Where should I look to verify this?
3. Does the evidence support the claim?
4. Can I fix this issue automatically?
5. How confident am I in this assessment?
</reasoning_approach>"""

    def _create_validation_prompt(self, component: Component, memory_bank_path: Path) -> str:
        """Create the validation prompt"""
        return f"""Validate and automatically fix the memory bank for component "{component.name}".

Component Details:
- Name: {component.name}
- Type: {component.type}
- Path: {component.path}
- Memory Bank Location: {memory_bank_path}

Your tasks:
1. **VALIDATION PHASE**:
   - Check completeness of all memory bank files
   - Verify accuracy against source code in {component.path}
   - Identify inconsistencies and issues
   - Score completeness and accuracy (0-100)

2. **AUTO-FIX PHASE**:
   - Automatically fix any issues you can resolve
   - Replace placeholder content with real analysis
   - Add missing files if needed
   - Correct inaccurate information
   - Ensure consistency across files

3. **REPORTING PHASE**:
   - Create detailed validation report
   - Document all fixes applied
   - Provide confidence scores

IMPORTANT: Focus on the component at {component.path} only. Don't analyze code outside this scope.

Start by reading the existing memory bank files, then validate against the source code."""

    async def validate_and_fix_component(
        self,
        component: Component,
        memory_bank_path: Path,
        repo_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns: int = 100
    ) -> ValidationResult:
        """
        Validate and fix a component's memory bank
        
        Args:
            component: Component to validate
            memory_bank_path: Path to the component's memory bank
            repo_path: Root path of the repository
            progress_callback: Optional callback for progress updates
            max_turns: Maximum turns for validation
            
        Returns:
            ValidationResult with validation and fix results
        """
        await self._call_progress_callback(
            progress_callback,
            f"[{component.name}] 🔍 Starting validation and auto-fix..."
        )
        
        # Create system prompt and validation prompt
        system_prompt = self._create_validation_system_prompt(component)
        validation_prompt = self._create_validation_prompt(component, memory_bank_path)
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=["Read", "Write", "Glob", "LS", "Grep", "Edit"],
            permission_mode="bypassPermissions",
        )
        
        turn_count = 0
        turn_warning_threshold = int(max_turns * 0.9)
        validation_report_created = False
        issues_found = []
        issues_fixed = []
        
        try:
            # Stream messages from Claude Code
            async for message in query(prompt=validation_prompt, options=options):
                turn_count += 1
                
                # Check if approaching turn limit
                if turn_count == turn_warning_threshold:
                    warning_msg = f"[{component.name}] ⚠️ Validation approaching turn limit ({turn_count}/{max_turns})"
                    await self._call_progress_callback(progress_callback, warning_msg)
                elif turn_count % 20 == 0:
                    await self._call_progress_callback(
                        progress_callback,
                        f"[{component.name}] Validation progress: {turn_count} turns"
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
                                    if file_path.endswith('validation_report.json'):
                                        validation_report_created = True
                                        await self._call_progress_callback(
                                            progress_callback,
                                            f"[{component.name}] 📊 Validation report created"
                                        )
                                    elif file_path.endswith('.md'):
                                        await self._call_progress_callback(
                                            progress_callback,
                                            f"[{component.name}] 🔧 Fixed: {Path(file_path).name}"
                                        )
                                elif tool_name == "Edit":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    await self._call_progress_callback(
                                        progress_callback,
                                        f"[{component.name}] ✏️ Edited: {Path(file_path).name}"
                                    )
                                elif tool_name == "Read":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    if 'memory-bank' in file_path:
                                        await self._call_progress_callback(
                                            progress_callback,
                                            f"[{component.name}] 📖 Validating: {Path(file_path).name}"
                                        )
            
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] Validation completed in {turn_count} turns"
            )
            
            # Parse validation report if created
            validation_report_path = memory_bank_path / "validation_report.json"
            if validation_report_created and validation_report_path.exists():
                with open(validation_report_path, 'r') as f:
                    report_data = json.load(f)
                
                # Parse issues
                for issue_data in report_data.get('issues', []):
                    issue = ValidationIssue(
                        severity=IssueSeverity(issue_data.get('severity', 'medium')),
                        issue_type=IssueType(issue_data.get('type', 'missing')),
                        file=issue_data.get('file', ''),
                        description=issue_data.get('description', ''),
                        evidence=issue_data.get('evidence', ''),
                        suggestion=issue_data.get('suggestion', ''),
                        auto_fixable=issue_data.get('auto_fixable', False)
                    )
                    issues_found.append(issue)
                    
                    # Check if this issue was marked as fixed
                    if issue_data.get('fixed', False):
                        issues_fixed.append(issue)
                
                # Parse verified claims
                verified_claims = []
                for claim_data in report_data.get('verified_claims', []):
                    claim = VerifiedClaim(
                        claim=claim_data.get('claim', ''),
                        source_file=claim_data.get('source_file', ''),
                        line_numbers=claim_data.get('line_numbers', ''),
                        verification_status=claim_data.get('verification_status', 'UNKNOWN')
                    )
                    verified_claims.append(claim)
                
                success = report_data.get('overall_status', 'FAIL') in ['PASS', 'PARTIAL']
                
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ✅ Validation {'passed' if success else 'completed'} - {len(issues_fixed)} fixes applied"
                )
                
                return ValidationResult(
                    component_name=component.name,
                    validation_timestamp=datetime.now().isoformat(),
                    overall_status=report_data.get('overall_status', 'FAIL'),
                    completeness_score=report_data.get('completeness_score', 0),
                    accuracy_score=report_data.get('accuracy_score', 0),
                    issues_found=issues_found,
                    issues_fixed=issues_fixed,
                    verified_claims=verified_claims,
                    fixes_applied=len(issues_fixed),
                    validation_metadata={
                        "turn_count": turn_count,
                        "max_turns": max_turns,
                        "component_type": component.type,
                        "component_path": component.path
                    }
                )
            else:
                # No validation report created
                await self._call_progress_callback(
                    progress_callback,
                    f"[{component.name}] ⚠️ No validation report created"
                )
                
                return ValidationResult(
                    component_name=component.name,
                    validation_timestamp=datetime.now().isoformat(),
                    overall_status="FAIL",
                    completeness_score=0,
                    accuracy_score=0,
                    issues_found=[],
                    issues_fixed=[],
                    verified_claims=[],
                    fixes_applied=0,
                    validation_metadata={
                        "turn_count": turn_count,
                        "error": "No validation report created"
                    }
                )
                
        except Exception as e:
            error_msg = f"Validation failed: {e}"
            logger.error(f"[{component.name}] {error_msg}")
            await self._call_progress_callback(
                progress_callback,
                f"[{component.name}] ❌ {error_msg}"
            )
            
            return ValidationResult(
                component_name=component.name,
                validation_timestamp=datetime.now().isoformat(),
                overall_status="FAIL",
                completeness_score=0,
                accuracy_score=0,
                issues_found=[],
                issues_fixed=[],
                verified_claims=[],
                fixes_applied=0,
                validation_metadata={
                    "turn_count": turn_count,
                    "error": str(e)
                }
            )
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)