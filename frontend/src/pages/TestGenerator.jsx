import React, { useState, useEffect } from 'react';
import {
  TestTube2,
  Copy,
  Check,
  RefreshCw,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export default function TestGenerator({
  selectedRepoId,
  selectedFileForTests
}) {
  const [files, setFiles] = useState([]);
  const [selectedFilePath, setSelectedFilePath] = useState(selectedFileForTests || '');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchFiles = async () => {
      if (!selectedRepoId) return;
      try {
        const fileList = await api.listRepositoryFiles(selectedRepoId);
        setFiles(fileList);
        if (!selectedFilePath && fileList.length > 0) {
          setSelectedFilePath(fileList[0].path);
        }
      } catch (err) {
        console.error('Error loading files:', err);
      }
    };
    fetchFiles();
  }, [selectedRepoId]);

  useEffect(() => {
    if (selectedFileForTests) {
      setSelectedFilePath(selectedFileForTests);
    }
  }, [selectedFileForTests]);

  // Update symbols when file changes
  useEffect(() => {
    const fileObj = files.find((f) => f.path === selectedFilePath);
    if (fileObj && fileObj.ast_symbols) {
      setAvailableSymbols(fileObj.ast_symbols);
    } else {
      setAvailableSymbols([]);
    }
    setSelectedSymbol('');
  }, [selectedFilePath, files]);

  const handleGenerate = async () => {
    if (!selectedRepoId || !selectedFilePath) return;
    setLoading(true);
    setTestResult(null);
    try {
      const res = await api.generateUnitTests(
        selectedRepoId,
        selectedFilePath,
        selectedSymbol || null
      );
      setTestResult(res);
    } catch (err) {
      alert(`Test generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (testResult?.generated_test_code) {
      navigator.clipboard.writeText(testResult.generated_test_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header & Controls */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <TestTube2 className="w-6 h-6 text-emerald-500" />
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Unit Test Generator</h1>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Generates comprehensive pytest & Jest suites covering happy paths, edge cases, invalid inputs, and exception assertions.
            </p>
          </div>

          {/* Selectors and Trigger */}
          <div className="flex flex-col sm:flex-row items-center gap-2">
            {/* File selector */}
            <select
              value={selectedFilePath}
              onChange={(e) => setSelectedFilePath(e.target.value)}
              className="text-xs font-mono bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-sky-500 w-full sm:w-64"
            >
              {files.map((f) => (
                <option key={f.id} value={f.path}>
                  {f.path} ({f.language})
                </option>
              ))}
            </select>

            {/* Target symbol selector */}
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="text-xs font-mono bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-sky-500 w-full sm:w-48"
            >
              <option value="">All functions in file</option>
              {availableSymbols.map((s, idx) => (
                <option key={idx} value={s.name}>
                  {s.kind}: {s.name}
                </option>
              ))}
            </select>

            <button
              onClick={handleGenerate}
              disabled={loading || !selectedFilePath}
              className="w-full sm:w-auto px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md shadow-emerald-500/20"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Synthesizing Tests...</span>
                </>
              ) : (
                <>
                  <TestTube2 className="w-3.5 h-3.5" />
                  <span>Generate Tests</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Safety & Execution Policy Notice */}
      <div className="p-3.5 rounded-xl bg-sky-50 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-900/50 text-sky-800 dark:text-sky-300 text-xs flex items-center space-x-2">
        <Info className="w-4 h-4 flex-shrink-0" />
        <span>
          <strong>Safe Execution Guarantee:</strong> Tests are synthesized based on actual source logic and parameter signatures. Never execute untrusted repository scripts on production hosts without reviewing test fixtures and mocking external dependencies.
        </span>
      </div>

      {/* Test Output Panel */}
      {testResult ? (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/50">
              <div className="flex items-center space-x-3 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
                  {testResult.file_path}
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-bold uppercase text-[10px]">
                  {testResult.framework}
                </span>
                {testResult.target_symbol && (
                  <span className="text-slate-500 font-mono">Target: {testResult.target_symbol}</span>
                )}
              </div>

              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 text-xs font-semibold flex items-center space-x-1.5 shadow-sm"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy Test Code'}</span>
              </button>
            </div>

            {/* Test Code Viewer */}
            <div className="bg-slate-950 p-4 font-mono text-xs text-slate-100 overflow-x-auto max-h-[500px]">
              <pre className="whitespace-pre-wrap">{testResult.generated_test_code}</pre>
            </div>

            {/* Assumptions & Notes */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 text-xs space-y-2">
              <span className="font-bold text-slate-800 dark:text-slate-200 block">Execution Assumptions:</span>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                {testResult.assumptions.map((a, idx) => (
                  <li key={idx}>{a}</li>
                ))}
              </ul>
              <p className="text-[11px] text-slate-400 mt-2">{testResult.execution_note}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-12 text-center text-slate-400 text-sm">
          Select a file and click "Generate Tests" to produce parameterized unit tests with pytest/Jest fixtures.
        </div>
      )}
    </div>
  );
}
