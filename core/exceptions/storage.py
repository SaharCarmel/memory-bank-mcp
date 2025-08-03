"""
Storage-related exceptions
"""

from .base import MemoryBankError


class StorageError(MemoryBankError):
    """Exception raised during storage operations"""
    pass


class MemoryBankNotFoundError(StorageError):
    """Exception raised when a memory bank is not found"""
    pass


class StorageAccessError(StorageError):
    """Exception raised when storage access fails"""
    pass


class FileSystemError(StorageError):
    """Exception raised during file system operations"""
    pass