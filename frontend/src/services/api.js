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
  },

  // Build job API methods
  async createBuildJob(buildRequest) {
    const response = await fetch(`${API_BASE_URL}/builds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(buildRequest),
    });
    if (!response.ok) {
      throw new Error('Failed to create build job');
    }
    return response.json();
  },

  async getBuildJobs() {
    const response = await fetch(`${API_BASE_URL}/builds`);
    if (!response.ok) {
      throw new Error('Failed to fetch build jobs');
    }
    return response.json();
  },

  async getBuildJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/builds/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch build job: ${jobId}`);
    }
    return response.json();
  },

  async getBuildJobStatus(jobId) {
    const response = await fetch(`${API_BASE_URL}/builds/${jobId}/status`);
    if (!response.ok) {
      throw new Error(`Failed to fetch build job status: ${jobId}`);
    }
    return response.json();
  },

  async cancelBuildJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/builds/${jobId}/cancel`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to cancel build job: ${jobId}`);
    }
    return response.json();
  }
};