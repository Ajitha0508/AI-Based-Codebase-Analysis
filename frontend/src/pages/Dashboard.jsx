import React, { useState } from 'react';
import {
  Github,
  Search,
  RefreshCw,
  FolderGit2,
  Trash2,
  ExternalLink,
  Layers,
  FileCode2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';

export default function Dashboard({
  repositories,
  refreshRepos,
  selectedRepoId,
  setSelectedRepoId,
  setActiveTab
}) {
  const [repoUrl, setRepoUrl] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Quick preset public repos
  const samplePresets = [
    { label: 'Flask', url: 'https://github.com/pallets/flask', desc: 'Lightweight WSGI Python web framework' },
    { label: 'FastAPI', url: 'https://github.com/tiangolo/fastapi', desc: 'Modern, fast web framework for Python APIs' },
    { label: 'Requests', url: 'https://github.com/psf/requests', desc: 'A simple, yet elegant, HTTP library' },
  ];

  const handleIndexSubmit = async (e) => {
    e?.preventDefault();
    if (!repoUrl.trim()) return;

    setIndexing(true);
    setErrorMessage(null);
    setStatusMessage('Validating GitHub repository and discovering source files...');

    try {
      const res = await api.indexRepository(repoUrl.trim(), forceRefresh);
      setStatusMessage(`Indexed ${res.file_count} files and generated ${res.chunk_count} vector chunks!`);
      setSelectedRepoId(res.id);
      await refreshRepos();
      setRepoUrl('');
    } catch (err) {
      setErrorMessage(err.message || 'Failed to index repository.');
    } finally {
      setIndexing(false);
    }
  };

  const handleDelete = async (repoId) => {
    if (!window.confirm(`Are you sure you want to delete the index for repository ${repoId}?`)) return;
    try {
      await api.deleteRepositoryIndex(repoId);
      if (selectedRepoId === repoId) {
        setSelectedRepoId(null);
      }
      await refreshRepos();
    } catch (err) {
      alert(`Error deleting index: ${err.message}`);
    }
  };

  const handleSelectAndNavigate = (repoId, tab = 'overview') => {
    setSelectedRepoId(repoId);
    setActiveTab(tab);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-sky-950 to-indigo-950 p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Retrieval-Augmented Generation for Codebases</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
            Understand, Search & Review Any GitHub Repository with Grounded AI
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
            CodeMind AI indexes public repositories, extracts language-aware AST symbols, chunks code preserving function boundaries, and anchors developer answers in verified source files with exact line numbers.
          </p>

          {/* Repository Ingestion Input Form */}
          <form onSubmit={handleIndexSubmit} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <Github className="absolute left-3.5 top-3.5 w-5 h-5 text-slate-400" />
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  disabled={indexing}
                  className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/10 dark:bg-slate-900/80 border border-white/20 text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 backdrop-blur"
                />
              </div>
              <button
                type="submit"
                disabled={indexing || !repoUrl.trim()}
                className="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-medium text-sm transition-all shadow-lg shadow-sky-500/30 flex items-center justify-center space-x-2"
              >
                {indexing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Indexing Codebase...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Analyze Repository</span>
                  </>
                )}
              </button>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-300 px-1">
              <label className="flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={forceRefresh}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                  className="rounded text-sky-500 focus:ring-sky-400"
                />
                <span>Force re-index if repository was already scanned</span>
              </label>
              <span>Public GitHub repositories supported</span>
            </div>
          </form>

          {/* Quick Presets */}
          <div className="mt-5 pt-4 border-t border-white/10 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400">Quick explore:</span>
            {samplePresets.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => setRepoUrl(p.url)}
                className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-slate-200 border border-white/10 transition-colors"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Status / Error feedback */}
          {statusMessage && (
            <div className="mt-4 p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}
          {errorMessage && (
            <div className="mt-4 p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-200 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>
      </div>

      {/* Indexed Repositories Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Indexed Repositories</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Persistent vector indexes stored in ChromaDB</p>
          </div>
          <button
            onClick={refreshRepos}
            className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            title="Refresh repository list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {repositories.length === 0 ? (
          <div className="text-center py-12 rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-8">
            <FolderGit2 className="w-12 h-12 mx-auto text-slate-400 mb-3" />
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No repositories indexed yet</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Enter a public GitHub URL above or select a preset to index your first codebase into the vector store.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {repositories.map((repo) => {
              const isSelected = selectedRepoId === repo.id;
              return (
                <div
                  key={repo.id}
                  className={`rounded-xl border transition-all p-5 flex flex-col justify-between ${
                    isSelected
                      ? 'bg-sky-50/50 dark:bg-sky-950/20 border-sky-400 dark:border-sky-700 shadow-md shadow-sky-500/10'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <FolderGit2 className="w-5 h-5 text-sky-600 dark:text-sky-400 flex-shrink-0" />
                        <h3 className="text-base font-bold text-slate-900 dark:text-white truncate">
                          {repo.owner}/{repo.name}
                        </h3>
                      </div>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                        repo.status === 'ready'
                          ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                          : 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
                      }`}>
                        {repo.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 line-clamp-2">
                      {repo.description || 'No description provided.'}
                    </p>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                      <div className="flex items-center space-x-1">
                        <FileCode2 className="w-3.5 h-3.5 text-slate-400" />
                        <span>{repo.file_count} files</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span>{repo.chunk_count} chunks</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[11px] font-mono">
                        {repo.primary_language || 'Code'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <button
                      onClick={() => handleSelectAndNavigate(repo.id, 'chat')}
                      className="text-xs font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-700 flex items-center space-x-1"
                    >
                      <span>Ask AI</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleSelectAndNavigate(repo.id, 'overview')}
                        className="px-2.5 py-1 text-xs rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium"
                      >
                        Overview
                      </button>
                      <button
                        onClick={() => handleDelete(repo.id)}
                        className="p-1 text-slate-400 hover:text-rose-500 rounded transition-colors"
                        title="Delete Index"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
