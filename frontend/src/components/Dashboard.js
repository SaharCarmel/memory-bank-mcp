import React from 'react';
import { Link } from 'react-router-dom';
import BuildPanel from './BuildPanel';

const Dashboard = ({ memoryBanks }) => {
  return (
    <div className="p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Memory Bank Dashboard</h1>
        <p className="text-gray-600 mt-2">Observability tool for memory banks</p>
      </header>

      {/* Build Jobs Panel */}
      <div className="mb-8">
        <BuildPanel />
      </div>

      {/* Memory Banks Grid */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Memory Banks</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {memoryBanks.map((bank) => (
            <div key={bank.name} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <Link to={`/memory-bank/${bank.name}`} className="block">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{bank.name}</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Files: {bank.file_count}</p>
                  <p>Tasks: {bank.task_count}</p>
                  <p>Changelog: {bank.has_changelog ? 'Yes' : 'No'}</p>
                  <p>Last updated: {new Date(bank.last_updated).toLocaleDateString()}</p>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {memoryBanks.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No memory banks found</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;