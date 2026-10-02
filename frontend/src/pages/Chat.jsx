import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  FileCode,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function Chat({ selectedRepoId, repositories }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I am **CodeMind AI**, your codebase assistant. I have indexed this repository's source code into ChromaDB and can explain its architecture, locate API endpoints, review logic, and trace cross-file dependencies with grounded file citations.",
      sources: [],
      supportingFiles: [],
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);

  const selectedRepo = repositories.find((r) => r.id === selectedRepoId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const exampleQuestions = [
    'Explain the overall architecture of this repository.',
    'Where is user authentication implemented?',
    'Which files handle database connections?',
    'Explain the dependencies in this project.',
    'Find potential bugs or unhandled edge cases.',
  ];

  const handleSend = async (queryText) => {
    const text = queryText || inputQuery;
    if (!text.trim() || loading || !selectedRepoId) return;

    const userMessageId = `user-${Date.now()}`;
    const newMessages = [
      ...messages,
      { id: userMessageId, role: 'user', content: text.trim() },
    ];
    setMessages(newMessages);
    setInputQuery('');
    setLoading(true);

    try {
      const resp = await api.askQuestion(selectedRepoId, text.trim(), 5);
      setMessages([
        ...newMessages,
        {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: resp.answer,
          sources: resp.sources || [],
          supportingFiles: resp.supporting_files_summary || [],
          insufficientEvidence: resp.insufficient_evidence,
        },
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Error communicating with assistant:** ${err.message}`,
          sources: [],
          supportingFiles: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSourceExpand = (msgId, srcIdx) => {
    const key = `${msgId}-${srcIdx}`;
    setExpandedSources((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const copyToClipboard = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 sm:px-6 flex flex-col h-[calc(100vh-140px)]">
      {/* Selected Repo Banner */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200 dark:border-slate-800 text-xs">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-500">Active Context:</span>
          <span className="px-2.5 py-1 rounded-md bg-sky-100 dark:bg-sky-950 font-mono font-bold text-sky-700 dark:text-sky-300">
            {selectedRepo ? `${selectedRepo.owner}/${selectedRepo.name}` : selectedRepoId}
          </span>
          {selectedRepo && (
            <span className="text-slate-400">({selectedRepo.file_count} files, {selectedRepo.chunk_count} chunks)</span>
          )}
        </div>
        <span className="text-slate-400 text-[11px] hidden sm:inline">Context Grounded • Cites File Lines</span>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-5 pr-2">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div key={msg.id} className={`flex items-start space-x-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center text-white flex-shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-3xl rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                  isUser
                    ? 'bg-sky-600 text-white rounded-tr-none'
                    : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none'
                }`}
              >
                {/* Markdown content rendering */}
                <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                {/* Insufficient Evidence Notice */}
                {msg.insufficientEvidence && (
                  <div className="mt-3 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-700 dark:text-amber-300 text-xs flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>The codebase does not contain explicit evidence for this query.</span>
                  </div>
                )}

                {/* Supporting Source Files References */}
                {!isUser && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                    <div className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2 flex items-center space-x-1">
                      <FileCode className="w-3.5 h-3.5 text-sky-500" />
                      <span>Retrieved Source Citations ({msg.sources.length}):</span>
                    </div>

                    <div className="space-y-2">
                      {msg.sources.map((src, sIdx) => {
                        const isExpanded = !!expandedSources[`${msg.id}-${sIdx}`];
                        return (
                          <div
                            key={sIdx}
                            className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 p-2.5 text-xs"
                          >
                            <div
                              onClick={() => toggleSourceExpand(msg.id, sIdx)}
                              className="flex items-center justify-between cursor-pointer"
                            >
                              <div className="flex items-center space-x-2 truncate">
                                <span className="font-mono font-semibold text-sky-600 dark:text-sky-400 truncate">
                                  {src.file_path}
                                </span>
                                <span className="text-slate-400">
                                  (lines {src.start_line}-{src.end_line})
                                </span>
                                {src.symbol_name && (
                                  <span className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[10px] font-mono">
                                    {src.symbol_name}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className="text-[10px] font-medium text-slate-500">
                                  {Math.round(src.similarity * 100)}% match
                                </span>
                                {isExpanded ? (
                                  <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                                ) : (
                                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                                )}
                              </div>
                            </div>

                            {isExpanded && (
                              <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-800 relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyToClipboard(src.content, `${msg.id}-${sIdx}`);
                                  }}
                                  className="absolute top-3 right-2 p-1 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-300"
                                  title="Copy snippet"
                                >
                                  {copiedIndex === `${msg.id}-${sIdx}` ? (
                                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                                  ) : (
                                    <Copy className="w-3.5 h-3.5" />
                                  )}
                                </button>
                                <pre className="p-2 rounded bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto max-h-48">
                                  {src.content}
                                </pre>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-white flex-shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center text-white flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="rounded-2xl rounded-tl-none p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center space-x-2 text-xs text-slate-500">
              <RefreshCw className="w-4 h-4 text-sky-500 animate-spin" />
              <span>Retrieving relevant chunks and constructing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Chips */}
      <div className="py-2 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1 whitespace-nowrap">
          <Sparkles className="w-3 h-3 text-sky-500" />
          <span>Suggestions:</span>
        </span>
        {exampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs whitespace-nowrap border border-slate-200 dark:border-slate-700 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="relative mt-1"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={`Ask anything about ${selectedRepo ? `${selectedRepo.owner}/${selectedRepo.name}` : 'the repository'}...`}
          disabled={loading || !selectedRepoId}
          className="w-full pl-4 pr-12 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 shadow-sm"
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim() || !selectedRepoId}
          className="absolute right-2 top-2 p-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white transition-all"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
