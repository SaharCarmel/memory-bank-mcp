import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const BuildPanel = () => {
  const [buildJobs, setBuildJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    type: 'build',
    repo_path: '',
    memory_bank_name: '',
    output_name: ''
  });

  useEffect(() => {
    loadBuildJobs();
    // Set up polling for job status updates
    const interval = setInterval(loadBuildJobs, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadBuildJobs = async () => {
    try {
      const jobs = await api.getBuildJobs();
      setBuildJobs(jobs);
    } catch (err) {
      console.error('Failed to load build jobs:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Client-side validation
    if (!formData.repo_path.trim()) {
      setError('Repository path is required');
      setLoading(false);
      return;
    }

    if (formData.type === 'update' && !formData.memory_bank_name.trim()) {
      setError('Memory bank name is required for update operations');
      setLoading(false);
      return;
    }

    try {
      const buildRequest = {
        type: formData.type,
        repo_path: formData.repo_path.trim(),
        ...(formData.memory_bank_name && { memory_bank_name: formData.memory_bank_name.trim() }),
        ...(formData.output_name && { output_name: formData.output_name.trim() })
      };

      await api.createBuildJob(buildRequest);
      setShowForm(false);
      setFormData({
        type: 'build',
        repo_path: '',
        memory_bank_name: '',
        output_name: ''
      });
      loadBuildJobs();
    } catch (err) {
      setError(err.message || 'Failed to create build job');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (jobId) => {
    try {
      await api.cancelBuildJob(jobId);
      loadBuildJobs();
    } catch (err) {
      console.error('Failed to cancel job:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Build Jobs</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          New Build Job
        </button>
      </div>

      {/* Build Form */}
      {showForm && (
        <div className="mb-6 p-4 border rounded-lg bg-gray-50">
          <h3 className="text-lg font-semibold mb-4">Create New Build Job</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="build">Build Memory Bank</option>
                  <option value="update">Update Memory Bank</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Repository Path
                </label>
                <input
                  type="text"
                  value={formData.repo_path}
                  onChange={(e) => setFormData({ ...formData, repo_path: e.target.value })}
                  placeholder="e.g., /path/to/repo"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {formData.type === 'update' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Memory Bank Name
                  </label>
                  <input
                    type="text"
                    value={formData.memory_bank_name}
                    onChange={(e) => setFormData({ ...formData, memory_bank_name: e.target.value })}
                    placeholder="e.g., my_project_memory_bank"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required={formData.type === 'update'}
                  />
                </div>
              )}

              {formData.type === 'build' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Output Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.output_name}
                    onChange={(e) => setFormData({ ...formData, output_name: e.target.value })}
                    placeholder="e.g., my_custom_memory_bank"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              )}
            </div>

            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-blue-300 transition-colors"
              >
                {loading ? 'Creating...' : 'Create Job'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Build Jobs List */}
      <div className="space-y-4">
        {buildJobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No build jobs found. Create your first build job to get started.
          </div>
        ) : (
          buildJobs
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map((job) => (
              <div key={job.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                      {job.status.toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-600 capitalize">{job.type}</span>
                  </div>
                  <div className="flex space-x-2">
                    {job.status === 'pending' && (
                      <button
                        onClick={() => handleCancel(job.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Cancel
                      </button>
                    )}
                    <span className="text-xs text-gray-500">
                      {formatDate(job.created_at)}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <span className="text-sm font-medium text-gray-700">Repository:</span>
                    <span className="text-sm text-gray-600 ml-2">{job.repo_path}</span>
                  </div>
                  {job.output_path && (
                    <div>
                      <span className="text-sm font-medium text-gray-700">Output:</span>
                      <span className="text-sm text-gray-600 ml-2">{job.output_path}</span>
                    </div>
                  )}
                </div>

                {job.error_message && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-3">
                    <span className="text-sm text-red-800">{job.error_message}</span>
                  </div>
                )}

                {job.logs && job.logs.length > 0 && (
                  <div className="bg-gray-900 text-gray-100 p-3 rounded-md font-mono text-xs max-h-32 overflow-y-auto">
                    {job.logs.slice(-5).map((log, index) => (
                      <div key={index}>{log}</div>
                    ))}
                  </div>
                )}
              </div>
            ))
        )}
      </div>
    </div>
  );
};

export default BuildPanel;