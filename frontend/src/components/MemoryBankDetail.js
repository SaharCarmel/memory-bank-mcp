import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../services/api';
import FileViewer from './FileViewer';
import ChangelogViewer from './ChangelogViewer';
import TaskList from './TaskList';

const MemoryBankDetail = () => {
  const { name } = useParams();
  const [memoryBank, setMemoryBank] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('files');

  const loadMemoryBank = async () => {
    try {
      setLoading(true);
      const bank = await api.getMemoryBank(name);
      setMemoryBank(bank);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemoryBank();
  }, [name]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500 text-xl">Error: {error}</div>
      </div>
    );
  }

  if (!memoryBank) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500 text-xl">Memory bank not found</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <header className="bg-white shadow-sm border-b border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">{memoryBank.name}</h1>
        <p className="text-gray-600 mt-1">{memoryBank.path}</p>
        <div className="flex items-center mt-4 space-x-6 text-sm text-gray-500">
          <span>Files: {memoryBank.files.length}</span>
          <span>Tasks: {memoryBank.tasks.length}</span>
          <span>Last updated: {new Date(memoryBank.updated_at).toLocaleDateString()}</span>
        </div>
      </header>

      <div className="flex-1 flex flex-col">
        <nav className="bg-gray-50 border-b border-gray-200">
          <div className="flex space-x-8 px-6">
            {['files', 'tasks', 'changelog'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize transition-colors ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </nav>

        <div className="flex-1 overflow-auto">
          {activeTab === 'files' && <FileViewer files={memoryBank.files} />}
          {activeTab === 'tasks' && <TaskList tasks={memoryBank.tasks} />}
          {activeTab === 'changelog' && <ChangelogViewer changelog={memoryBank.changelog} />}
        </div>
      </div>
    </div>
  );
};

export default MemoryBankDetail;