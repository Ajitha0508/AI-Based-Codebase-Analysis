import React from 'react';
import {
  Code2,
  FolderGit2,
  MessageSquare,
  FileCode,
  ShieldAlert,
  TestTube2,
  BookOpen,
  TrendingUp,
  Settings,
  Sun,
  Moon,
  Github,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  darkMode,
  setDarkMode,
  repositories,
  selectedRepoId,
  setSelectedRepoId,
  healthStatus
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: FolderGit2 },
    { id: 'overview', label: 'Overview', icon: BookOpen, requiresRepo: true },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare, requiresRepo: true },
    { id: 'explorer', label: 'Code Explorer', icon: FileCode, requiresRepo: true },
    { id: 'review', label: 'Code Review', icon: ShieldAlert, requiresRepo: true },
    { id: 'tests', label: 'Unit Tests', icon: TestTube2, requiresRepo: true },
    { id: 'docs', label: 'Documentation', icon: BookOpen, requiresRepo: true },
    { id: 'benchmarks', label: 'Velocity', icon: TrendingUp },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
              <Code2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">CodeMind AI</span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                  RAG
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Codebase Intelligence Assistant</p>
            </div>
          </div>

          {/* Active Repository Selector */}
          <div className="hidden md:flex items-center space-x-2">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Target Repo:</span>
            <select
              value={selectedRepoId || ''}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {repositories.length === 0 ? (
                <option value="">No repositories indexed</option>
              ) : (
                repositories.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.owner}/{r.name} ({r.file_count} files)
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Controls: Theme & System Status */}
          <div className="flex items-center space-x-3">
            {/* System Status Pill */}
            <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
              {healthStatus?.status === 'ok' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Ready ({healthStatus.active_llm_provider})</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                  <span>Backend Offline</span>
                </>
              )}
            </div>

            {/* Dark / Light Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              title="Toggle Theme"
            >
              {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto py-2 scrollbar-none border-t border-slate-100 dark:border-slate-800/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const disabled = item.requiresRepo && !selectedRepoId;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                disabled={disabled}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  active
                    ? 'bg-sky-50 dark:bg-sky-950/80 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800'
                    : disabled
                    ? 'text-slate-400 dark:text-slate-600 cursor-not-allowed opacity-60'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${active ? 'text-sky-600 dark:text-sky-400' : ''}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
