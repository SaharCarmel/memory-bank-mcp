from typing import List, Optional
from app.adapters.filesystem import FileSystemAdapter
from app.models.memory_bank import MemoryBank, MemoryBankSummary

class MemoryBankService:
    def __init__(self, root_path: str):
        self.adapter = FileSystemAdapter(root_path)
    
    def get_all_memory_banks(self) -> List[MemoryBankSummary]:
        """Get summaries of all memory banks"""
        return self.adapter.get_memory_banks()
    
    def get_memory_bank(self, name: str) -> Optional[MemoryBank]:
        """Get detailed information for a specific memory bank"""
        return self.adapter.get_memory_bank(name)
    
    def get_memory_bank_files(self, name: str) -> List[str]:
        """Get list of files in a memory bank"""
        memory_bank = self.adapter.get_memory_bank(name)
        if not memory_bank:
            return []
        return [f.name for f in memory_bank.files]
    
    def get_memory_bank_file_content(self, name: str, filename: str) -> Optional[str]:
        """Get content of a specific file in a memory bank"""
        memory_bank = self.adapter.get_memory_bank(name)
        if not memory_bank:
            return None
        
        for file in memory_bank.files:
            if file.name == filename:
                return file.content
        
        return None