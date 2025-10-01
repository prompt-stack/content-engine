// ============================================================================
// API Response Types - Content Engine
// ============================================================================

// ----------------------------------------------------------------------------
// Health & System
// ----------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  environment: string;
  features?: {
    openai: boolean;
    anthropic: boolean;
    gemini: boolean;
    deepseek: boolean;
    gmail?: boolean;
    tavily?: boolean;
    default_llm: string;
  };
}

// ----------------------------------------------------------------------------
// Extractors
// ----------------------------------------------------------------------------

export interface ExtractRequest {
  url: string;
  max_comments?: number; // For Reddit
}

export interface ExtractedContent {
  platform: string;
  url: string;
  source: string;
  title?: string;
  author?: string;
  content?: string;
  published_at?: string;
  metadata?: Record<string, unknown>;
  extracted_at: string;
}

// ----------------------------------------------------------------------------
// LLM
// ----------------------------------------------------------------------------

export interface LLMProvider {
  name: string;
  models: string[];
  available: boolean;
}

export interface LLMProvidersResponse {
  providers: LLMProvider[];
  default_provider: string;
}

export interface LLMRequest {
  prompt: string;
  provider?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  system_prompt?: string;
}

export interface LLMResponse {
  provider: string;
  model: string;
  result: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  finish_reason?: string;
}

export type ProcessingTask =
  | 'summarize'
  | 'extract_key_points'
  | 'analyze_sentiment'
  | 'generate_tags'
  | 'extract_entities';

export interface ProcessContentRequest {
  content: string;
  task: ProcessingTask;
  provider?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ProcessContentResponse {
  task: ProcessingTask;
  provider: string;
  model: string;
  result: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// ----------------------------------------------------------------------------
// Media / Image Generation
// ----------------------------------------------------------------------------

export type ImageProvider = 'openai' | 'gemini';

export interface MediaProvider {
  name: string;
  models: string[];
  available: boolean;
}

export interface MediaProvidersResponse {
  providers: MediaProvider[];
  default_provider: string;
}

export interface GenerateImageRequest {
  prompt: string;
  provider?: ImageProvider;
  model?: string;
  size?: string; // e.g., "1024x1024"
  quality?: 'standard' | 'hd';
  style?: 'vivid' | 'natural';
  temperature?: number;
}

export interface GeneratedImage {
  provider: string;
  model: string;
  prompt: string;
  image_url: string;
  revised_prompt?: string;
  created_at: string;
}

export interface GenerateFromContentRequest {
  content: string;
  provider?: ImageProvider;
  prompt_template?: string;
}

// ----------------------------------------------------------------------------
// Search
// ----------------------------------------------------------------------------

export type SearchDepth = 'basic' | 'advanced';

export interface SearchCapabilities {
  provider: string;
  features: string[];
  max_results: number;
  supports_domains: boolean;
  supports_images: boolean;
}

export interface SearchRequest {
  query: string;
  search_depth?: SearchDepth;
  max_results?: number;
  include_domains?: string[];
  exclude_domains?: string[];
  include_answer?: boolean;
  include_images?: boolean;
}

export interface SearchResult {
  title: string;
  url: string;
  content: string;
  score?: number;
  published_date?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  answer?: string;
  images?: string[];
  search_depth: SearchDepth;
  results_count: number;
}

export interface SearchContextRequest {
  content_summary: string;
  max_results?: number;
}

export interface TrendingSearchRequest {
  topic: string;
  platforms?: ('reddit' | 'twitter' | 'tiktok' | 'youtube' | 'medium' | 'substack')[];
  max_results?: number;
}

export interface FactCheckRequest {
  claim: string;
  max_results?: number;
}

export interface NewsSearchRequest {
  topic: string;
  recency?: '24h' | '7d' | '30d';
  max_results?: number;
}

export interface ResearchSearchRequest {
  research_topic: string;
  academic?: boolean;
  max_results?: number;
}

// ----------------------------------------------------------------------------
// Prompts
// ----------------------------------------------------------------------------

export interface Prompt {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  template: string;
  variables: string[];
  output_format: string;
  estimated_tokens: number;
}

export interface PromptCategory {
  id: string;
  name: string;
  icon: string;
}

export interface RenderPromptRequest {
  prompt_id: string;
  variables: Record<string, string>;
}

export interface RenderPromptResponse {
  prompt_id: string;
  rendered_prompt: string;
}

// ----------------------------------------------------------------------------
// Error Responses
// ----------------------------------------------------------------------------

export interface APIError {
  detail: string;
  status?: number;
}