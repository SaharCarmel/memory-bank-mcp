import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = ({ memoryBanks, selectedMemoryBank, onMemoryBankSelect }) => {
  const location = useLocation();

  return (
    <div className="bg-gray-800 text-white w-64 flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <Link to="/" className="text-xl font-bold">
          Memory Bank Dashboard
        </Link>
      </div>
      
      <nav className="flex-1 overflow-y-auto">
        <div className="p-4">
          <Link
            to="/"
            className={`block py-2 px-4 rounded mb-2 transition-colors ${
              location.pathname === '/' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            Dashboard
          </Link>
        </div>
        
        <div className="px-4 pb-4">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">
            Memory Banks
          </h3>
          <div className="space-y-1">
            {memoryBanks.map((bank) => (
              <Link
                key={bank.name}
                to={`/memory-bank/${bank.name}`}
                onClick={() => onMemoryBankSelect(bank.name)}
                className={`block py-2 px-4 rounded text-sm transition-colors ${
                  selectedMemoryBank === bank.name
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <div className="font-medium">{bank.name}</div>
                <div className="text-xs text-gray-400">
                  {bank.file_count} files · {bank.task_count} tasks
                </div>
              </Link>
            ))}
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;