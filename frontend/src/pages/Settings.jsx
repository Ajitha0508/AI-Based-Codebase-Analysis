import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  CheckCircle2,
  XCircle,
  KeyRound,
  Database,
  Layers,
  Sliders,
  RefreshCw,
  Terminal,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings() {
  const [settingsData, setSettingsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const res = await api.getSettings();
        setSettingsData(res);
      } catch (err) {
        console.error('Failed to load settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  if (loading && !settingsData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-6 h-6 text-sky-500 animate-spin mr-2" />
        <span className="text-sm text-slate-500">Loading system settings...</span>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
        <div className="flex items-center space-x-2">
          <SettingsIcon className="w-6 h-6 text-sky-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">System Settings & AI Providers</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Operational configurations, provider integration statuses, and vector database persistence.
        </p>
      </div>

      {/* AI Providers Card */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <KeyRound className="w-4 h-4 text-sky-500" />
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">LLM Provider Status</h2>
          </div>
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-semibold">
            Active: {settingsData?.llm_provider || 'local'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {/* Local Mode */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 dark:text-slate-200">Local Engine</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Offline AST matching & synthesis. 100% operational without API keys.</p>
          </div>

          {/* Gemini */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 dark:text-slate-200">Google Gemini</span>
              {settingsData?.is_gemini_configured ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <XCircle className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {settingsData?.is_gemini_configured ? 'API key active in .env' : 'Unconfigured (GEMINI_API_KEY)'}
            </p>
          </div>

          {/* OpenAI */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 dark:text-slate-200">OpenAI</span>
              {settingsData?.is_openai_configured ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <XCircle className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {settingsData?.is_openai_configured ? 'API key active in .env' : 'Unconfigured (OPENAI_API_KEY)'}
            </p>
          </div>

          {/* Groq */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 dark:text-slate-200">Groq Cloud</span>
              {settingsData?.is_groq_configured ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <XCircle className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {settingsData?.is_groq_configured ? 'API key active in .env' : 'Unconfigured (GROQ_API_KEY)'}
            </p>
          </div>
        </div>
      </div>

      {/* RAG & Vector Storage Specs */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <Sliders className="w-4 h-4 text-indigo-500" />
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">RAG Chunking & Retrieval Specs</h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Chunk Size</span>
            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
              {settingsData?.chunk_size || 800} chars
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Chunk Overlap</span>
            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
              {settingsData?.chunk_overlap || 100} chars
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Retrieval Top-K</span>
            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
              {settingsData?.retrieval_top_k || 5} chunks
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Max File Size</span>
            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
              {settingsData?.max_file_size_kb || 500} KB
            </span>
          </div>
        </div>
      </div>

      {/* Configuration Instructions */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-3">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-slate-400" />
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">Configuring Cloud AI Keys</h2>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          To switch from the local deterministic engine to Gemini, OpenAI, or Groq, edit <code className="font-mono text-sky-600 dark:text-sky-400">backend/.env</code> and restart the backend server:
        </p>

        <div className="p-3 rounded-xl bg-slate-950 font-mono text-xs text-slate-200 overflow-x-auto">
          <pre>{`# In backend/.env:
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Or for OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_api_key_here`}</pre>
        </div>
      </div>
    </div>
  );
}
