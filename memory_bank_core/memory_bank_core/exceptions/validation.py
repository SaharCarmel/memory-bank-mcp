"""
Validation-related exceptions
"""

from .base import MemoryBankError


class ValidationError(MemoryBankError):
    """Exception raised during validation operations"""
    pass


class InvalidRepositoryError(ValidationError):
    """Exception raised when repository structure is invalid"""
    pass


class InvalidMemoryBankError(ValidationError):
    """Exception raised when memory bank structure is invalid"""
    pass


class ConfigurationError(ValidationError):
    """Exception raised when configuration is invalid"""
    pass