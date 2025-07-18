const API_BASE_URL = 'http://localhost:8888/api';

export const api = {
  async getMemoryBanks() {
    const response = await fetch(`${API_BASE_URL}/memory-banks`);
    if (!response.ok) {
      throw new Error('Failed to fetch memory banks');
    }
    return response.json();
  },

  async getMemoryBank(name) {
    const response = await fetch(`${API_BASE_URL}/memory-banks/${name}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch memory bank: ${name}`);
    }
    return response.json();
  },

  async getMemoryBankFiles(name) {
    const response = await fetch(`${API_BASE_URL}/memory-banks/${name}/files`);
    if (!response.ok) {
      throw new Error(`Failed to fetch files for memory bank: ${name}`);
    }
    return response.json();
  },

  async getMemoryBankFileContent(name, filename) {
    const response = await fetch(`${API_BASE_URL}/memory-banks/${name}/files/${filename}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch file content: ${filename}`);
    }
    return response.json();
  }
};