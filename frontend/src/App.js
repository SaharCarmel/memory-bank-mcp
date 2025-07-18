import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import MemoryBankDetail from './components/MemoryBankDetail';
import Sidebar from './components/Sidebar';
import { api } from './services/api';

function App() {
  const [memoryBanks, setMemoryBanks] = useState([]);
  const [selectedMemoryBank, setSelectedMemoryBank] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMemoryBanks();
  }, []);

  const loadMemoryBanks = async () => {
    try {
      setLoading(true);
      const banks = await api.getMemoryBanks();
      setMemoryBanks(banks);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMemoryBankSelect = (bankName) => {
    setSelectedMemoryBank(bankName);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-500 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar 
          memoryBanks={memoryBanks}
          selectedMemoryBank={selectedMemoryBank}
          onMemoryBankSelect={handleMemoryBankSelect}
        />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard memoryBanks={memoryBanks} />} />
            <Route path="/memory-bank/:name" element={<MemoryBankDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;