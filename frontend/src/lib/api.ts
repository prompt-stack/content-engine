import type {
  HealthResponse,
  ExtractedContent,
  LLMProvidersResponse,
  LLMRequest,
  LLMResponse,
  ProcessContentRequest,
  ProcessContentResponse,
  MediaProvidersResponse,
  GenerateImageRequest,
  GeneratedImage,
  GenerateFromContentRequest,
  SearchCapabilities,
  SearchRequest,
  SearchResponse,
  SearchContextRequest,
  TrendingSearchRequest,
  FactCheckRequest,
  NewsSearchRequest,
  ResearchSearchRequest,
  Prompt,
  PromptCategory,
  RenderPromptRequest,
  RenderPromptResponse,
  Capture,
  CaptureListRequest,
  CaptureSearchRequest,
  APIError,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9765';

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Parse error response, handling both JSON and non-JSON responses
 */
async function parseError(response: Response): Promise<string> {
  try {
    const error: APIError = await response.json();
    return error.detail || `Request failed with status ${response.status}`;
  } catch {
    // Response wasn't JSON, return generic error
    return `Request failed with status ${response.status}`;
  }
}

/**
 * Get Clerk session token for authenticated requests
 */
async function getAuthToken(): Promise<string | null> {
  try {
    // Check if we're in a browser environment and Clerk is available
    if (typeof window !== 'undefined' && (window as any).Clerk) {
      const session = await (window as any).Clerk.session?.getToken();
      return session || null;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Generic API request wrapper with error handling and auth
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    // Get auth token from Clerk
    const token = await getAuthToken();

    // Build headers with conditional Authorization
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options?.headers,
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorMessage = await parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unexpected error occurred');
  }
}

// ============================================================================
// API Client
// ============================================================================

export const api = {
  // --------------------------------------------------------------------------
  // Health & System
  // --------------------------------------------------------------------------

  health: (): Promise<HealthResponse> => {
    return apiRequest<HealthResponse>('/health');
  },

  // --------------------------------------------------------------------------
  // Extractors
  // --------------------------------------------------------------------------

  extract: {
    tiktok: (url: string): Promise<ExtractedContent> => {
      return apiRequest<ExtractedContent>('/api/extract/tiktok', {
        method: 'POST',
        body: JSON.stringify({ url }),
      });
    },

    youtube: (url: string): Promise<ExtractedContent> => {
      return apiRequest<ExtractedContent>('/api/extract/youtube', {
        method: 'POST',
        body: JSON.stringify({ url }),
      });
    },

    reddit: (url: string, max_comments = 20, title?: string): Promise<ExtractedContent> => {
      return apiRequest<ExtractedContent>('/api/extract/reddit', {
        method: 'POST',
        body: JSON.stringify({ url, max_comments, title }),
      });
    },

    article: (url: string): Promise<ExtractedContent> => {
      return apiRequest<ExtractedContent>('/api/extract/article', {
        method: 'POST',
        body: JSON.stringify({ url }),
      });
    },

    auto: (url: string): Promise<ExtractedContent> => {
      return apiRequest<ExtractedContent>('/api/extract/auto', {
        method: 'POST',
        body: JSON.stringify({ url }),
      });
    },
  },

  // --------------------------------------------------------------------------
  // LLM
  // --------------------------------------------------------------------------

  llm: {
    providers: (): Promise<LLMProvidersResponse> => {
      return apiRequest<LLMProvidersResponse>('/api/llm/providers');
    },

    generate: (request: Partial<LLMRequest>): Promise<LLMResponse> => {
      const defaults: LLMRequest = {
        prompt: request.prompt || '',
        provider: request.provider || 'deepseek',
        max_tokens: request.max_tokens || 500,
        temperature: request.temperature || 0.7,
      };
      return apiRequest<LLMResponse>('/api/llm/generate', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    processContent: (request: Partial<ProcessContentRequest>): Promise<ProcessContentResponse> => {
      const defaults: ProcessContentRequest = {
        content: request.content || '',
        task: request.task || 'summarize',
        provider: request.provider || 'deepseek',
        max_tokens: request.max_tokens || 500,
        temperature: request.temperature || 0.7,
      };
      return apiRequest<ProcessContentResponse>('/api/llm/process-content', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },
  },

  // --------------------------------------------------------------------------
  // Media / Image Generation
  // --------------------------------------------------------------------------

  media: {
    providers: (): Promise<MediaProvidersResponse> => {
      return apiRequest<MediaProvidersResponse>('/api/media/providers');
    },

    generateImage: (request: Partial<GenerateImageRequest>): Promise<GeneratedImage> => {
      const defaults: GenerateImageRequest = {
        prompt: request.prompt || '',
        provider: request.provider || 'openai',
      };
      return apiRequest<GeneratedImage>('/api/media/generate-image', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    generateFromContent: (request: Partial<GenerateFromContentRequest>): Promise<GeneratedImage> => {
      const defaults: GenerateFromContentRequest = {
        content: request.content || '',
        provider: request.provider || 'openai',
      };
      return apiRequest<GeneratedImage>('/api/media/generate-from-content', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },
  },

  // --------------------------------------------------------------------------
  // Search
  // --------------------------------------------------------------------------

  search: {
    capabilities: (): Promise<SearchCapabilities> => {
      return apiRequest<SearchCapabilities>('/api/search/capabilities');
    },

    search: (request: Partial<SearchRequest>): Promise<SearchResponse> => {
      const defaults: SearchRequest = {
        query: request.query || '',
        search_depth: request.search_depth || 'advanced',
        max_results: request.max_results || 10,
      };
      return apiRequest<SearchResponse>('/api/search/search', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    context: (request: Partial<SearchContextRequest>): Promise<SearchResponse> => {
      const defaults: SearchContextRequest = {
        content_summary: request.content_summary || '',
        max_results: request.max_results || 5,
      };
      return apiRequest<SearchResponse>('/api/search/context', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    trending: (request: Partial<TrendingSearchRequest>): Promise<SearchResponse> => {
      const defaults: TrendingSearchRequest = {
        topic: request.topic || '',
        max_results: request.max_results || 10,
      };
      return apiRequest<SearchResponse>('/api/search/trending', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    factCheck: (request: Partial<FactCheckRequest>): Promise<SearchResponse> => {
      const defaults: FactCheckRequest = {
        claim: request.claim || '',
        max_results: request.max_results || 5,
      };
      return apiRequest<SearchResponse>('/api/search/fact-check', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    news: (request: Partial<NewsSearchRequest>): Promise<SearchResponse> => {
      const defaults: NewsSearchRequest = {
        topic: request.topic || '',
        recency: request.recency || '7d',
        max_results: request.max_results || 10,
      };
      return apiRequest<SearchResponse>('/api/search/news', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },

    research: (request: Partial<ResearchSearchRequest>): Promise<SearchResponse> => {
      const defaults: ResearchSearchRequest = {
        research_topic: request.research_topic || '',
        academic: request.academic || false,
        max_results: request.max_results || 10,
      };
      return apiRequest<SearchResponse>('/api/search/research', {
        method: 'POST',
        body: JSON.stringify({ ...defaults, ...request }),
      });
    },
  },

  prompts: {
    list: (category?: string): Promise<Prompt[]> => {
      const params = category ? `?category=${encodeURIComponent(category)}` : '';
      return apiRequest<Prompt[]>(`/api/prompts/list${params}`);
    },

    categories: (): Promise<PromptCategory[]> => {
      return apiRequest<PromptCategory[]>('/api/prompts/categories');
    },

    get: (promptId: string): Promise<Prompt> => {
      return apiRequest<Prompt>(`/api/prompts/${promptId}`);
    },

    render: (request: RenderPromptRequest): Promise<RenderPromptResponse> => {
      return apiRequest<RenderPromptResponse>('/api/prompts/render', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
  },

  // --------------------------------------------------------------------------
  // Captures / Content Vault
  // --------------------------------------------------------------------------

  capture: {
    list: (params?: CaptureListRequest): Promise<Capture[]> => {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.offset) queryParams.append('offset', params.offset.toString());
      const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
      return apiRequest<Capture[]>(`/api/capture/list${query}`);
    },

    search: (params: CaptureSearchRequest): Promise<Capture[]> => {
      const queryParams = new URLSearchParams();
      queryParams.append('q', params.q);
      if (params.limit) queryParams.append('limit', params.limit.toString());
      return apiRequest<Capture[]>(`/api/capture/search?${queryParams.toString()}`);
    },

    get: (id: number): Promise<Capture> => {
      return apiRequest<Capture>(`/api/capture/${id}`);
    },

    delete: (id: number): Promise<void> => {
      return apiRequest<void>(`/api/capture/${id}`, { method: 'DELETE' });
    },

    count: (): Promise<{ user_id: number; total_captures: number }> => {
      return apiRequest<{ user_id: number; total_captures: number }>('/api/capture/stats/count');
    },
  },

  // --------------------------------------------------------------------------
  // Newsletters
  // --------------------------------------------------------------------------

  newsletters: {
    extractions: (): Promise<any[]> => {
      return apiRequest<any[]>('/api/newsletters/extractions');
    },

    extractionStatus: (extractionId: string): Promise<any> => {
      return apiRequest<any>(`/api/newsletters/extractions/${extractionId}/status`);
    },

    extract: (params: {
      days_back?: number;
      hours_back?: number;
      max_results?: number;
      senders?: string[];
    }): Promise<{ status: string; extraction_id: string; message: string }> => {
      return apiRequest('/api/newsletters/extract', {
        method: 'POST',
        body: JSON.stringify(params),
      });
    },

    config: (): Promise<any> => {
      return apiRequest<any>('/api/newsletters/config');
    },

    updateConfig: (config: any): Promise<{ status: string; message: string }> => {
      return apiRequest('/api/newsletters/config', {
        method: 'PUT',
        body: JSON.stringify(config),
      });
    },

    testUrl: (url: string): Promise<{ url: string; is_valid: boolean; reason: string }> => {
      return apiRequest('/api/newsletters/config/test-url', {
        method: 'POST',
        body: JSON.stringify({ url }),
      });
    },
  },
};