"""
Backward compatibility layer for transition period
Allows bash scripts to still work while testing new backend integration
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class BackwardCompatibilityMode:
    """
    Provides fallback to bash scripts during migration period
    Can be enabled via environment variable: USE_LEGACY_SCRIPTS=true
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if backward compatibility mode is enabled"""
        return os.getenv("USE_LEGACY_SCRIPTS", "false").lower() == "true"
    
    @staticmethod
    async def execute_legacy_build(
        root_path: Path,
        repo_path: str,
        output_name: str,
        logs: List[str]
    ) -> dict:
        """Execute build using legacy bash script"""
        build_script = root_path / "build_memory_bank.sh"
        
        if not build_script.exists():
            raise FileNotFoundError("Legacy build script not found")
            
        cmd = ["bash", str(build_script), repo_path, output_name]
        logs.append(f"[LEGACY MODE] Executing: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            cwd=str(root_path),
            capture_output=True,
            text=True
        )
        
        if process.stdout:
            logs.extend(process.stdout.strip().split('\n'))
        if process.stderr:
            logs.extend(process.stderr.strip().split('\n'))
            
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, 
                cmd, 
                f"Legacy script failed with return code {process.returncode}"
            )
            
        return {
            "success": True,
            "output_path": str(root_path / output_name),
            "mode": "legacy_bash_script"
        }
    
    @staticmethod
    async def execute_legacy_update(
        root_path: Path,
        repo_path: str,
        memory_bank_name: str,
        logs: List[str]
    ) -> dict:
        """Execute update using legacy bash script"""
        update_script = root_path / "update_memory_bank.sh"
        
        if not update_script.exists():
            raise FileNotFoundError("Legacy update script not found")
            
        cmd = ["bash", str(update_script), repo_path, memory_bank_name]
        logs.append(f"[LEGACY MODE] Executing: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            cwd=str(root_path),
            capture_output=True,
            text=True
        )
        
        if process.stdout:
            logs.extend(process.stdout.strip().split('\n'))
        if process.stderr:
            logs.extend(process.stderr.strip().split('\n'))
            
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, 
                cmd, 
                f"Legacy script failed with return code {process.returncode}"
            )
            
        return {
            "success": True,
            "memory_bank_name": memory_bank_name,
            "mode": "legacy_bash_script"
        }