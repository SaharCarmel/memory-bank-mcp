"""
Build-related exceptions
"""

from .base import MemoryBankError


class BuildError(MemoryBankError):
    """Exception raised during memory bank build operations"""
    pass


class BuildTimeoutError(BuildError):
    """Exception raised when build operation times out"""
    pass


class RepositoryValidationError(BuildError):
    """Exception raised when repository validation fails"""
    pass


class ClaudeIntegrationError(BuildError):
    """Exception raised when Claude integration fails"""
    pass