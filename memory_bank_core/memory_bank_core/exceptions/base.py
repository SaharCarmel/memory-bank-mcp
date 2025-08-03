"""
Base exception class for memory bank operations
"""


class MemoryBankError(Exception):
    """Base exception for all memory bank operations"""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message