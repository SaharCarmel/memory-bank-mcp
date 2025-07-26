#!/usr/bin/env python3
"""
Entry point for running memory_bank_core as a module
"""

import sys
from pathlib import Path

# Add parent directory to path if running from within the package directory
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    # Try relative import first (when run as module)
    from .main import cli
except ImportError:
    # Fall back to absolute import (when run directly)
    from memory_bank_core.main import cli

if __name__ == "__main__":
    cli()
