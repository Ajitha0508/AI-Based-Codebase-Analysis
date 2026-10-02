import React, { useEffect, useState } from 'react';
import {
  FolderGit2,
  GitBranch,
  GitCommit,
  FileCode2,
  Layers,
  RefreshCw,
  Trash2,
  ExternalLink,
  MessageSquare,
  ShieldAlert,
  TestTube2,
  BookOpen,
  PieChart
} from 'lucide-react';
import { api } from '../services/api';

export default function RepoOverview({
  selectedRepoId,
  setActiveTab,
  refreshRepos
}) {
  const [repo, setRepo] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDetails = async () => {
    if (!selectedRepoId) return;
    setLoading(true);
    setError(null);
    try {
      const [repoData, filesData] = await Promise.all([
        api.getRepository(selectedRepoId),
        api.listRepositoryFiles(selectedRepoId),
      ]);
      setRepo(repoData);
      setFiles(filesData);
    } catch (err) {
      setError(err.message || 'Failed to load repository details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [selectedRepoId]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshRepository(selectedRepoId);
      await fetchDetails();
      await refreshRepos();
    } catch (err) {
      alert(`Refresh failed: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete the vector index and files for ${selectedRepoId}?`)) return;
    try {
      await api.deleteRepositoryIndex(selectedRepoId);
      await refreshRepos();
      setActiveTab('dashboard');
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-6 h-6 text-sky-500 animate-spin" />
        <span className="ml-2 text-sm text-slate-500">Loading repository overview...</span>
      </div>
    );
  }

  if (error || !repo) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <p className="text-rose-500 text-sm mb-4">{error || 'Repository not found'}</p>
        <button
          onClick={() => setActiveTab('dashboard')}
          className="px-4 py-2 bg-slate-800 text-white text-xs rounded-lg font-medium"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  // Calculate language distribution
  const langCounts = {};
  files.forEach((f) => {
    const lang = f.language || 'text';
    langCounts[lang] = (langCounts[lang] || 0) + 1;
  });
  const totalFiles = files.length || 1;
  const langDistribution = Object.entries(langCounts)
    .map(([lang, count]) => ({
      lang,
      count,
      pct: ((count / totalFiles) * 100).toFixed(1),
    }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header Card */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <div className="w-12 h-12 rounded-xl bg-sky-100 dark:bg-sky-950 flex items-center justify-center text-sky-600 dark:text-sky-400 flex-shrink-0">
              <FolderGit2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  {repo.owner}/{repo.name}
                </h1>
                <a
                  href={repo.url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  title="View on GitHub"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
                {repo.description || 'Public GitHub repository indexed by CodeMind AI.'}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh Index</span>
            </button>
            <button
              onClick={handleDelete}
              className="px-3.5 py-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900 hover:bg-rose-100 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Index</span>
            </button>
          </div>
        </div>

        {/* Git Info Bar */}
        <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Default Branch</span>
            <div className="flex items-center space-x-1.5 font-medium text-slate-800 dark:text-slate-200 mt-0.5">
              <GitBranch className="w-3.5 h-3.5 text-slate-400" />
              <span>{repo.default_branch}</span>
            </div>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Indexed Commit SHA</span>
            <div className="flex items-center space-x-1.5 font-mono text-slate-800 dark:text-slate-200 mt-0.5">
              <GitCommit className="w-3.5 h-3.5 text-slate-400" />
              <span>{repo.commit_sha ? repo.commit_sha.slice(0, 8) : 'latest'}</span>
            </div>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Vector Storage</span>
            <div className="flex items-center space-x-1.5 font-medium text-slate-800 dark:text-slate-200 mt-0.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>ChromaDB (Isolated)</span>
            </div>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Indexing Status</span>
            <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
              {repo.status.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Scanned Files</span>
            <FileCode2 className="w-5 h-5 text-sky-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{repo.file_count}</div>
          <p className="text-[11px] text-slate-400 mt-1">Eligible text source files excluding binaries & secrets</p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Indexed Code Chunks</span>
            <Layers className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{repo.chunk_count}</div>
          <p className="text-[11px] text-slate-400 mt-1">Language-aware AST chunks in vector database</p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Supported Languages</span>
            <PieChart className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{langDistribution.length}</div>
          <p className="text-[11px] text-slate-400 mt-1">Discovered programming & markup languages</p>
        </div>
      </div>

      {/* Language Breakdown */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3 flex items-center space-x-2">
          <span>Language Distribution</span>
        </h3>
        
        {/* Visual Progress Bar */}
        <div className="w-full h-3 rounded-full bg-slate-100 dark:bg-slate-800 flex overflow-hidden mb-4">
          {langDistribution.map((item, idx) => {
            const colors = ['bg-sky-500', 'bg-indigo-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500', 'bg-purple-500'];
            const color = colors[idx % colors.length];
            return (
              <div
                key={item.lang}
                style={{ width: `${item.pct}%` }}
                className={`h-full ${color}`}
                title={`${item.lang}: ${item.pct}%`}
              />
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3">
          {langDistribution.map((item) => (
            <div key={item.lang} className="flex items-center space-x-1.5 text-xs">
              <span className="font-semibold text-slate-700 dark:text-slate-300 capitalize">{item.lang}:</span>
              <span className="text-slate-500 dark:text-slate-400">{item.count} files ({item.pct}%)</span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Assistant Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => setActiveTab('chat')}
          className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 dark:hover:border-sky-500 text-left transition-all group"
        >
          <MessageSquare className="w-5 h-5 text-sky-500 mb-2 group-hover:scale-110 transition-transform" />
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">Ask AI Questions</h4>
          <p className="text-xs text-slate-500 mt-1">Get grounded answers with source file line numbers</p>
        </button>

        <button
          onClick={() => setActiveTab('explorer')}
          className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 dark:hover:border-sky-500 text-left transition-all group"
        >
          <FileCode2 className="w-5 h-5 text-indigo-500 mb-2 group-hover:scale-110 transition-transform" />
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">Explore Codebase</h4>
          <p className="text-xs text-slate-500 mt-1">Browse files, inspect AST symbols, and view code</p>
        </button>

        <button
          onClick={() => setActiveTab('review')}
          className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 dark:hover:border-sky-500 text-left transition-all group"
        >
          <ShieldAlert className="w-5 h-5 text-rose-500 mb-2 group-hover:scale-110 transition-transform" />
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">Code Review</h4>
          <p className="text-xs text-slate-500 mt-1">Static AST rules and AI security & quality review</p>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 dark:hover:border-sky-500 text-left transition-all group"
        >
          <TestTube2 className="w-5 h-5 text-emerald-500 mb-2 group-hover:scale-110 transition-transform" />
          <h4 className="text-sm font-bold text-slate-900 dark:text-white">Unit Test Generator</h4>
          <p className="text-xs text-slate-500 mt-1">Generate comprehensive pytest & Jest suites</p>
        </button>
      </div>
    </div>
  );
}
