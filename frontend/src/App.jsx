import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import RepoOverview from './pages/RepoOverview';
import Chat from './pages/Chat';
import CodeExplorer from './pages/CodeExplorer';
import CodeReview from './pages/CodeReview';
import TestGenerator from './pages/TestGenerator';
import DocGenerator from './pages/DocGenerator';
import VelocityBenchmarks from './pages/VelocityBenchmarks';
import Settings from './pages/Settings';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedRepoId, setSelectedRepoId] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [darkMode, setDarkMode] = useState(true);

  // Cross-screen navigation states
  const [selectedFileForReview, setSelectedFileForReview] = useState('');
  const [selectedFileForTests, setSelectedFileForTests] = useState('');

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Load repositories and health status
  const refreshRepos = async () => {
    try {
      const [repoList, health] = await Promise.all([
        api.listRepositories(),
        api.getHealth(),
      ]);
      setRepositories(repoList);
      setHealthStatus(health);

      // Auto-select first repo if none selected and repos exist
      if (!selectedRepoId && repoList.length > 0) {
        setSelectedRepoId(repoList[0].id);
      }
    } catch (err) {
      console.warn('Backend not responding yet:', err);
    }
  };

  useEffect(() => {
    refreshRepos();
    const interval = setInterval(refreshRepos, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        repositories={repositories}
        selectedRepoId={selectedRepoId}
        setSelectedRepoId={setSelectedRepoId}
        healthStatus={healthStatus}
      />

      <main className="flex-1 pb-12">
        {activeTab === 'dashboard' && (
          <Dashboard
            repositories={repositories}
            refreshRepos={refreshRepos}
            selectedRepoId={selectedRepoId}
            setSelectedRepoId={setSelectedRepoId}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'overview' && (
          <RepoOverview
            selectedRepoId={selectedRepoId}
            setActiveTab={setActiveTab}
            refreshRepos={refreshRepos}
          />
        )}

        {activeTab === 'chat' && (
          <Chat
            selectedRepoId={selectedRepoId}
            repositories={repositories}
          />
        )}

        {activeTab === 'explorer' && (
          <CodeExplorer
            selectedRepoId={selectedRepoId}
            setActiveTab={setActiveTab}
            setSelectedFileForReview={setSelectedFileForReview}
            setSelectedFileForTests={setSelectedFileForTests}
          />
        )}

        {activeTab === 'review' && (
          <CodeReview
            selectedRepoId={selectedRepoId}
            selectedFileForReview={selectedFileForReview}
          />
        )}

        {activeTab === 'tests' && (
          <TestGenerator
            selectedRepoId={selectedRepoId}
            selectedFileForTests={selectedFileForTests}
          />
        )}

        {activeTab === 'docs' && (
          <DocGenerator
            selectedRepoId={selectedRepoId}
          />
        )}

        {activeTab === 'benchmarks' && (
          <VelocityBenchmarks />
        )}

        {activeTab === 'settings' && (
          <Settings />
        )}
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>CodeMind AI — Grounded Codebase Assistant Using RAG • Built with React, FastAPI, ChromaDB & AST Parsing</p>
      </footer>
    </div>
  );
}
