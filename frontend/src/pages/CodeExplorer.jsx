import React, { useState, useEffect } from 'react';
import {
  FileCode,
  Search,
  Code,
  ShieldAlert,
  TestTube2,
  Copy,
  Check,
  RefreshCw,
  FolderTree,
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

export default function CodeExplorer({
  selectedRepoId,
  setActiveTab,
  setSelectedFileForReview,
  setSelectedFileForTests
}) {
  const [files, setFiles] = useState([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [loadingContent, setLoadingContent] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchFiles = async () => {
      if (!selectedRepoId) return;
      setLoadingFiles(true);
      try {
        const data = await api.listRepositoryFiles(selectedRepoId);
        setFiles(data);
        if (data.length > 0) {
          setSelectedFile(data[0]);
        }
      } catch (err) {
        console.error('Failed to load files:', err);
      } finally {
        setLoadingFiles(false);
      }
    };
    fetchFiles();
  }, [selectedRepoId]);

  useEffect(() => {
    const fetchContent = async () => {
      if (!selectedRepoId || !selectedFile) return;
      setLoadingContent(true);
      try {
        const res = await api.getFileContent(selectedRepoId, selectedFile.path);
        setFileContent(res.content || '');
      } catch (err) {
        setFileContent(`// Error loading file content: ${err.message}`);
      } finally {
        setLoadingContent(false);
      }
    };
    fetchContent();
  }, [selectedRepoId, selectedFile]);

  const filteredFiles = files.filter((f) =>
    f.path.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const handleCopyCode = () => {
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const navigateToReview = () => {
    if (selectedFile) {
      setSelectedFileForReview(selectedFile.path);
      setActiveTab('review');
    }
  };

  const navigateToTests = () => {
    if (selectedFile) {
      setSelectedFileForTests(selectedFile.path);
      setActiveTab('tests');
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
        {/* Left Sidebar: File Browser */}
        <div className="md:col-span-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col overflow-hidden shadow-sm">
          <div className="p-3 border-b border-slate-200 dark:border-slate-800">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search files..."
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 border-none text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span>{filteredFiles.length} indexed files</span>
              <span>Click to view</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/50">
            {loadingFiles ? (
              <div className="p-6 text-center text-xs text-slate-500">
                <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2 text-sky-500" />
                Loading files...
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">No matching files found.</div>
            ) : (
              filteredFiles.map((file) => {
                const isSelected = selectedFile?.path === file.path;
                return (
                  <button
                    key={file.id}
                    onClick={() => setSelectedFile(file)}
                    className={`w-full p-2.5 text-left flex items-center justify-between text-xs transition-colors ${
                      isSelected
                        ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 font-semibold'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileCode className={`w-4 h-4 flex-shrink-0 ${isSelected ? 'text-sky-600' : 'text-slate-400'}`} />
                      <span className="truncate font-mono">{file.path}</span>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 flex-shrink-0 ml-2">
                      {file.line_count}L
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Panel: Source Code Viewer & AST Symbols */}
        <div className="md:col-span-8 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col overflow-hidden shadow-sm">
          {selectedFile ? (
            <>
              {/* Header Bar */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold font-mono text-slate-900 dark:text-white truncate">
                    {selectedFile.path}
                  </h3>
                  <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                    <span className="capitalize">{selectedFile.language}</span>
                    <span>•</span>
                    <span>{selectedFile.line_count} lines</span>
                    <span>•</span>
                    <span>{(selectedFile.size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={navigateToReview}
                    className="px-2.5 py-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900 text-xs font-semibold flex items-center space-x-1 hover:bg-rose-100 transition-colors"
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Review</span>
                  </button>
                  <button
                    onClick={navigateToTests}
                    className="px-2.5 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 text-xs font-semibold flex items-center space-x-1 hover:bg-emerald-100 transition-colors"
                  >
                    <TestTube2 className="w-3.5 h-3.5" />
                    <span>Generate Tests</span>
                  </button>
                  <button
                    onClick={handleCopyCode}
                    className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 text-xs"
                    title="Copy Code"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* AST Symbols Bar (if symbols exist) */}
              {selectedFile.ast_symbols && selectedFile.ast_symbols.length > 0 && (
                <div className="px-4 py-2 bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 flex items-center gap-1.5 overflow-x-auto scrollbar-none text-xs">
                  <span className="text-[11px] font-semibold text-slate-400 flex-shrink-0">AST Symbols:</span>
                  {selectedFile.ast_symbols.map((sym, sIdx) => (
                    <span
                      key={sIdx}
                      className="px-2 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sky-600 dark:text-sky-400 font-mono text-[11px] whitespace-nowrap"
                    >
                      {sym.kind}: {sym.name} (L{sym.start_line})
                    </span>
                  ))}
                </div>
              )}

              {/* Code Viewer with Line Numbers */}
              <div className="flex-1 overflow-auto bg-slate-950 p-4 font-mono text-xs text-slate-200">
                {loadingContent ? (
                  <div className="flex items-center justify-center h-full text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mr-2 text-sky-500" />
                    Loading file contents...
                  </div>
                ) : (
                  <div className="flex">
                    {/* Line numbers */}
                    <div className="pr-4 select-none text-slate-600 text-right font-mono border-r border-slate-800 mr-4">
                      {fileContent.split('\n').map((_, i) => (
                        <div key={i}>{i + 1}</div>
                      ))}
                    </div>
                    {/* Code text */}
                    <pre className="flex-1 overflow-x-auto whitespace-pre font-mono text-slate-200">
                      {fileContent}
                    </pre>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400 text-sm">
              Select a file from the list to view its source code and symbols.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
