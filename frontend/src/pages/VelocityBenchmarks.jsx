import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  FileCheck,
  RefreshCw,
  Info,
  Layers,
  ArrowRight
} from 'lucide-react';
import { api } from '../services/api';

export default function VelocityBenchmarks() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form states for new live record
  const [taskName, setTaskName] = useState('');
  const [workflowType, setWorkflowType] = useState('AI-Assisted');
  const [durationMinutes, setDurationMinutes] = useState(15);
  const [testsRun, setTestsRun] = useState(10);
  const [testsPassed, setTestsPassed] = useState(10);
  const [reviewFindings, setReviewFindings] = useState(1);
  const [correctionsRequired, setCorrectionsRequired] = useState(0);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchBenchmarks = async () => {
    setLoading(true);
    try {
      const res = await api.getBenchmarks();
      setData(res);
    } catch (err) {
      console.error('Error fetching velocity benchmarks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, []);

  const handleRecordSubmit = async (e) => {
    e.preventDefault();
    if (!taskName.trim()) return;

    setSubmitting(true);
    try {
      await api.recordBenchmark({
        task_name: taskName.trim(),
        workflow_type: workflowType,
        duration_seconds: parseFloat(durationMinutes) * 60,
        tests_run: parseInt(testsRun, 10),
        tests_passed: parseInt(testsPassed, 10),
        review_findings_count: parseInt(reviewFindings, 10),
        corrections_required: parseInt(correctionsRequired, 10),
        notes: notes.trim(),
      });
      setIsModalOpen(false);
      setTaskName('');
      setNotes('');
      await fetchBenchmarks();
    } catch (err) {
      alert(`Failed to save benchmark: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-6 h-6 text-sky-500 animate-spin mr-2" />
        <span className="text-sm text-slate-500">Loading velocity benchmarks...</span>
      </div>
    );
  }

  const summary = data?.summary || {};
  const manual = data?.manual_metrics || {};
  const ai = data?.ai_metrics || {};

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header and Modal Trigger */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-6 h-6 text-indigo-500" />
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">Developer Velocity Benchmarking</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Empirical comparative evaluation between Manual developer workflows and AI-Assisted development cycles.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-indigo-500/20"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Record Benchmark Run</span>
        </button>
      </div>

      {/* Methodology Notice */}
      <div className="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs flex items-center space-x-2">
        <Info className="w-4 h-4 text-indigo-500 flex-shrink-0" />
        <span>
          <strong>Methodology Note:</strong> Velocity measurements are calculated using actual recorded task durations and test pass records. Sample baseline entries are tagged with <code className="font-mono bg-slate-200 dark:bg-slate-700 px-1 rounded">[Sample Baseline]</code>.
        </span>
      </div>

      {/* Top Level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Time Saved */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <span className="text-xs font-medium text-slate-500">Average Time Saved</span>
          <div className="mt-2 text-2xl font-bold text-indigo-600 dark:text-indigo-400">
            {summary.time_saved_minutes_avg || 0} min
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            ~{summary.speedup_percentage || 0}% faster cycle duration
          </p>
        </div>

        {/* AI Test Pass Rate */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <span className="text-xs font-medium text-slate-500">AI Test Pass Rate</span>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {ai.test_pass_rate_pct || 0}%
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Manual pass rate: {manual.test_pass_rate_pct || 0}%
          </p>
        </div>

        {/* Review Corrections Required */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <span className="text-xs font-medium text-slate-500">Review Corrections Required</span>
          <div className="mt-2 text-2xl font-bold text-sky-600 dark:text-sky-400">
            {ai.total_corrections_required || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Manual corrections: {manual.total_corrections_required || 0}
          </p>
        </div>

        {/* Total Benchmark Runs */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <span className="text-xs font-medium text-slate-500">Recorded Observations</span>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {summary.total_recorded_runs || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {summary.manual_runs_count || 0} Manual vs {summary.ai_runs_count || 0} AI
          </p>
        </div>
      </div>

      {/* Side-by-Side Comparison Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Manual Workflow Card */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">Manual Workflow Baseline</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {manual.count || 0} tasks
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Average Duration:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{manual.avg_duration_minutes || 0} minutes</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Total Tests Executed:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{manual.total_tests_run || 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Tests Passed:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{manual.total_tests_passed || 0} ({manual.test_pass_rate_pct || 0}%)</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Post-Review Corrections:</span>
              <span className="font-bold text-rose-600">{manual.total_corrections_required || 0}</span>
            </div>
          </div>
        </div>

        {/* AI-Assisted Workflow Card */}
        <div className="rounded-2xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/20 dark:bg-indigo-950/20 p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-indigo-100 dark:border-indigo-900/40">
            <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-300">CodeMind AI-Assisted Workflow</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
              {ai.count || 0} tasks
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Average Duration:</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400">{ai.avg_duration_minutes || 0} minutes</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Total Tests Executed:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">{ai.total_tests_run || 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Tests Passed:</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400">{ai.total_tests_passed || 0} ({ai.test_pass_rate_pct || 0}%)</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Post-Review Corrections:</span>
              <span className="font-bold text-emerald-600">{ai.total_corrections_required || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Task Comparison Table */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Task-by-Task Comparison Table</h3>
          <span className="text-xs text-slate-400">Paired observation metrics</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-3">Task Name</th>
                <th className="p-3">Manual Duration</th>
                <th className="p-3">AI Duration</th>
                <th className="p-3">Time Delta</th>
                <th className="p-3">Tests Passed (AI)</th>
                <th className="p-3">Data Origin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {data?.task_comparisons?.map((t, idx) => {
                const manualTime = t.manual?.duration_minutes ?? 'N/A';
                const aiTime = t.ai?.duration_minutes ?? 'N/A';
                const timeDiff =
                  t.manual && t.ai
                    ? `${(t.manual.duration_minutes - t.ai.duration_minutes).toFixed(1)}m faster`
                    : 'N/A';

                return (
                  <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">{t.task_name}</td>
                    <td className="p-3 text-slate-500">{manualTime !== 'N/A' ? `${manualTime}m` : '—'}</td>
                    <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">
                      {aiTime !== 'N/A' ? `${aiTime}m` : '—'}
                    </td>
                    <td className="p-3 font-semibold text-indigo-600 dark:text-indigo-400">{timeDiff}</td>
                    <td className="p-3 text-slate-600 dark:text-slate-300">
                      {t.ai ? `${t.ai.tests_passed}/${t.ai.tests_run}` : '—'}
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-mono text-slate-500">
                        {t.manual?.is_sample || t.ai?.is_sample ? 'Sample Baseline' : 'Live Recorded'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Live Benchmark Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Record New Velocity Measurement</h3>
            <p className="text-xs text-slate-500">Log task execution duration, test results, and correction metrics.</p>

            <form onSubmit={handleRecordSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium mb-1">Task Name / Feature</label>
                <input
                  type="text"
                  required
                  value={taskName}
                  onChange={(e) => setTaskName(e.target.value)}
                  placeholder="e.g. Implement OAuth JWT verification middleware"
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium mb-1">Workflow Type</label>
                  <select
                    value={workflowType}
                    onChange={(e) => setWorkflowType(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  >
                    <option value="AI-Assisted">AI-Assisted</option>
                    <option value="Manual">Manual</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    min="1"
                    step="0.5"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium mb-1">Tests Run / Passed</label>
                  <div className="flex space-x-1">
                    <input
                      type="number"
                      min="0"
                      value={testsRun}
                      onChange={(e) => setTestsRun(e.target.value)}
                      placeholder="Run"
                      className="w-1/2 p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                    />
                    <input
                      type="number"
                      min="0"
                      value={testsPassed}
                      onChange={(e) => setTestsPassed(e.target.value)}
                      placeholder="Passed"
                      className="w-1/2 p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium mb-1">Review Findings / Fixes</label>
                  <div className="flex space-x-1">
                    <input
                      type="number"
                      min="0"
                      value={reviewFindings}
                      onChange={(e) => setReviewFindings(e.target.value)}
                      placeholder="Findings"
                      className="w-1/2 p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                    />
                    <input
                      type="number"
                      min="0"
                      value={correctionsRequired}
                      onChange={(e) => setCorrectionsRequired(e.target.value)}
                      placeholder="Corrections"
                      className="w-1/2 p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block font-medium mb-1">Notes (Optional)</label>
                <textarea
                  rows="2"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Observations, roadblocks, or specific AI prompts used..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !taskName.trim()}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center space-x-1"
                >
                  {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Save Record</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
