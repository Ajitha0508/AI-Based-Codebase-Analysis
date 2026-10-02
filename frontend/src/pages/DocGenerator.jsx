import React, { useState } from 'react';
import {
  BookOpen,
  Copy,
  Check,
  RefreshCw,
  FileText,
  Layers,
  Terminal,
  Code2
} from 'lucide-react';
import { api } from '../services/api';

export default function DocGenerator({ selectedRepoId }) {
  const [docType, setDocType] = useState('overview');
  const [docResult, setDocResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const docTypes = [
    { id: 'overview', label: 'Architecture Overview', icon: Layers, desc: 'High-level architectural diagrams & patterns' },
    { id: 'module', label: 'Module Documentation', icon: FileText, desc: 'Component and package interface breakdown' },
    { id: 'api', label: 'API Reference', icon: Code2, desc: 'Endpoints, handlers, and schema models' },
    { id: 'setup', label: 'Setup & Installation Guide', icon: Terminal, desc: 'Verified commands based on repo files' },
    { id: 'readme', label: 'Suggested README', icon: BookOpen, desc: 'Complete GitHub README with feature summary' },
  ];

  const handleGenerate = async () => {
    if (!selectedRepoId) return;
    setLoading(true);
    setDocResult(null);
    try {
      const res = await api.generateDocumentation(selectedRepoId, docType);
      setDocResult(res);
    } catch (err) {
      alert(`Documentation generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (docResult?.markdown_content) {
      navigator.clipboard.writeText(docResult.markdown_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header Card */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <BookOpen className="w-6 h-6 text-sky-500" />
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Documentation Generator</h1>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Grounded technical documentation, architecture overviews, and API references generated from verified codebase files.
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !selectedRepoId}
            className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md shadow-sky-500/20"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Compiling Documentation...</span>
              </>
            ) : (
              <>
                <BookOpen className="w-3.5 h-3.5" />
                <span>Generate Documentation</span>
              </>
            )}
          </button>
        </div>

        {/* Doc Type Selector Chips */}
        <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          {docTypes.map((t) => {
            const Icon = t.icon;
            const isSelected = docType === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setDocType(t.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'bg-sky-50 dark:bg-sky-950/40 border-sky-400 dark:border-sky-700 shadow-sm'
                    : 'bg-slate-50/50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700/60 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Icon className={`w-4 h-4 mb-1.5 ${isSelected ? 'text-sky-600 dark:text-sky-400' : 'text-slate-400'}`} />
                <div className={`text-xs font-bold ${isSelected ? 'text-sky-900 dark:text-sky-200' : 'text-slate-800 dark:text-slate-200'}`}>
                  {t.label}
                </div>
                <div className="text-[10px] text-slate-500 line-clamp-1 mt-0.5">{t.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Output Markdown Preview */}
      {docResult ? (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/50">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {docResult.doc_type} • {docResult.repo_name}
            </span>

            <button
              onClick={handleCopy}
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 text-xs font-semibold flex items-center space-x-1.5 shadow-sm"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied Markdown' : 'Copy Markdown'}</span>
            </button>
          </div>

          <div className="p-6 overflow-y-auto max-h-[600px] text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans whitespace-pre-wrap">
            {docResult.markdown_content}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-12 text-center text-slate-400 text-sm">
          Choose a documentation format and click "Generate Documentation" to create grounded Markdown specifications.
        </div>
      )}
    </div>
  );
}
