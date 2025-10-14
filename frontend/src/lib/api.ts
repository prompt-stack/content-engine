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
 * Generic API request wrapper with error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
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
};