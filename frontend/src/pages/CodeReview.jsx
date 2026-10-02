import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Copy,
  Check,
  RefreshCw,
  FileCode,
  Info,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function CodeReview({
  selectedRepoId,
  selectedFileForReview,
}) {
  const [files, setFiles] = useState([]);
  const [selectedFilePath, setSelectedFilePath] = useState(selectedFileForReview || '');
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [humanApproved, setHumanApproved] = useState({});

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
        console.error('Error fetching files:', err);
      }
    };
    fetchFiles();
  }, [selectedRepoId]);

  useEffect(() => {
    if (selectedFileForReview) {
      setSelectedFilePath(selectedFileForReview);
    }
  }, [selectedFileForReview]);

  const handleRunReview = async () => {
    if (!selectedRepoId || !selectedFilePath) return;
    setLoading(true);
    setReviewData(null);
    try {
      const res = await api.reviewCode(selectedRepoId, selectedFilePath);
      setReviewData(res);
    } catch (err) {
      alert(`Review failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const copyFix = (fixText, idx) => {
    navigator.clipboard.writeText(fixText);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const toggleApproval = (idx) => {
    setHumanApproved((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getSeverityBadgeClass = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-950/70 text-red-700 dark:text-red-300 border-red-300 dark:border-red-800';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-950/70 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-800';
      case 'medium':
        return 'bg-amber-100 dark:bg-amber-950/70 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800';
      default:
        return 'bg-sky-100 dark:bg-sky-950/70 text-sky-700 dark:text-sky-300 border-sky-300 dark:border-sky-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header and Controls */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-6 h-6 text-rose-500" />
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Security & Code Review</h1>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Combines deterministic static AST security analysis with intelligent AI maintainability review.
            </p>
          </div>

          {/* File selector & Action */}
          <div className="flex flex-col sm:flex-row items-center gap-2">
            <select
              value={selectedFilePath}
              onChange={(e) => setSelectedFilePath(e.target.value)}
              className="text-xs font-mono bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-sky-500 w-full sm:w-72"
            >
              {files.map((f) => (
                <option key={f.id} value={f.path}>
                  {f.path} ({f.language})
                </option>
              ))}
            </select>

            <button
              onClick={handleRunReview}
              disabled={loading || !selectedFilePath}
              className="w-full sm:w-auto px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md shadow-rose-500/20"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing Code...</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Run Code Review</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Severity Metrics Bar (if reviewed) */}
        {reviewData && (
          <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/40">
              <span className="text-[11px] font-bold text-red-600 uppercase">Critical</span>
              <div className="text-xl font-extrabold text-red-700 dark:text-red-400 mt-0.5">
                {reviewData.severity_counts.Critical || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/40">
              <span className="text-[11px] font-bold text-orange-600 uppercase">High</span>
              <div className="text-xl font-extrabold text-orange-700 dark:text-orange-400 mt-0.5">
                {reviewData.severity_counts.High || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40">
              <span className="text-[11px] font-bold text-amber-600 uppercase">Medium</span>
              <div className="text-xl font-extrabold text-amber-700 dark:text-amber-400 mt-0.5">
                {reviewData.severity_counts.Medium || 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-sky-50 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-900/40">
              <span className="text-[11px] font-bold text-sky-600 uppercase">Low</span>
              <div className="text-xl font-extrabold text-sky-700 dark:text-sky-400 mt-0.5">
                {reviewData.severity_counts.Low || 0}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Human Review Notice */}
      <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-300 text-xs flex items-center space-x-2">
        <Info className="w-4 h-4 flex-shrink-0" />
        <span>
          <strong>Human Review Policy:</strong> Automated findings are potential concerns and heuristics. No code changes are automatically applied. Always inspect and test before modifying production code.
        </span>
      </div>

      {/* Findings List */}
      {reviewData ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Total Findings: {reviewData.total_findings} in {reviewData.file_path}
            </span>
            <span>Distinguishes Static AST vs AI Suggestions</span>
          </div>

          {reviewData.findings.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center">
              <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">No issues flagged!</h3>
              <p className="text-xs text-slate-500 mt-1">No security vulnerabilities or code smells identified in this file.</p>
            </div>
          ) : (
            reviewData.findings.map((finding, idx) => {
              const isApproved = !!humanApproved[idx];
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${getSeverityBadgeClass(finding.severity)}`}>
                        {finding.severity}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        {finding.title}
                      </h3>
                    </div>

                    <div className="flex items-center space-x-2 text-xs">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
                        L{finding.line_range}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-sky-600 dark:text-sky-400 font-semibold text-[11px]">
                        {finding.verification_status}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                    {finding.explanation}
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 text-xs">
                    <span className="font-semibold text-slate-800 dark:text-slate-200 block mb-1">Why it matters:</span>
                    <p className="text-slate-600 dark:text-slate-400">{finding.why_it_matters}</p>
                  </div>

                  {finding.suggested_fix && (
                    <div className="p-3 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs relative">
                      <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-[11px] text-slate-400 font-sans">
                        <span>Suggested Remediation:</span>
                        <button
                          onClick={() => copyFix(finding.suggested_fix, idx)}
                          className="flex items-center space-x-1 text-slate-300 hover:text-white"
                        >
                          {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedIndex === idx ? 'Copied' : 'Copy Fix'}</span>
                        </button>
                      </div>
                      <pre className="whitespace-pre-wrap">{finding.suggested_fix}</pre>
                    </div>
                  )}

                  {/* Human Verification Toggle */}
                  <div className="pt-2 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 text-xs">
                    <label className="flex items-center space-x-2 cursor-pointer select-none text-slate-600 dark:text-slate-400">
                      <input
                        type="checkbox"
                        checked={isApproved}
                        onChange={() => toggleApproval(idx)}
                        className="rounded text-sky-600 focus:ring-sky-500"
                      />
                      <span>Mark as verified by developer</span>
                    </label>
                    <span className="text-[11px] text-slate-400">
                      Category: {finding.category}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-12 text-center text-slate-400 text-sm">
          Select a file and click "Run Code Review" to perform static AST security checks and AI quality analysis.
        </div>
      )}
    </div>
  );
}
