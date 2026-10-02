/**
 * CodeMind AI API Client Service
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMessage = data.detail || `Request failed with status ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Health & Settings
  getHealth: () => request('/health'),
  getSettings: () => request('/settings'),

  // Repositories
  indexRepository: (url, forceRefresh = false) =>
    request('/repositories/index', {
      method: 'POST',
      body: JSON.stringify({ url, force_refresh: forceRefresh }),
    }),

  listRepositories: () => request('/repositories'),

  getRepository: (id) => request(`/repositories/${encodeURIComponent(id)}`),

  refreshRepository: (id) =>
    request(`/repositories/${encodeURIComponent(id)}/refresh`, {
      method: 'POST',
    }),

  deleteRepositoryIndex: (id) =>
    request(`/repositories/${encodeURIComponent(id)}/index`, {
      method: 'DELETE',
    }),

  listRepositoryFiles: (id, language = '') => {
    const query = language ? `?language=${encodeURIComponent(language)}` : '';
    return request(`/repositories/${encodeURIComponent(id)}/files${query}`);
  },

  getFileContent: (id, path) =>
    request(`/repositories/${encodeURIComponent(id)}/files/content?path=${encodeURIComponent(path)}`),

  // RAG Chat
  askQuestion: (repositoryId, query, topK = 5) =>
    request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        query,
        top_k: topK,
      }),
    }),

  // Code Review
  reviewCode: (repositoryId, filePath, codeOverride = null) =>
    request('/code-review', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        file_path: filePath,
        code_override: codeOverride,
      }),
    }),

  // Unit Test Generation
  generateUnitTests: (repositoryId, filePath, symbolName = null) =>
    request('/test-generation', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        file_path: filePath,
        symbol_name: symbolName,
      }),
    }),

  // Documentation Generation
  generateDocumentation: (repositoryId, docType = 'overview') =>
    request('/documentation', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        doc_type: docType,
      }),
    }),

  // Velocity Benchmarks
  getBenchmarks: () => request('/benchmarks'),

  recordBenchmark: (benchmarkData) =>
    request('/benchmarks', {
      method: 'POST',
      body: JSON.stringify(benchmarkData),
    }),
};
