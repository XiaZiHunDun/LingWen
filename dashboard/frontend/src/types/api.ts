/**
 * Core API types for LingWen Dashboard
 * Provides type definitions for API responses and requests
 */

/** Generic API response wrapper */
export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  code?: number;
}

/** Error response from backend */
export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  code?: string;
}

/** Request options */
export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  signal?: AbortSignal;
  retries?: number;
  headers?: Record<string, string>;
}

/** Overview data from backend */
export interface OverviewData {
  slug?: string;
  name?: string;
  creation_mode?: string;
  chapters_written?: number;
  total_chapters?: number;
  word_count?: number;
  [key: string]: unknown;
}

/** Studio summary */
export interface StudioSummary {
  slug?: string;
  name?: string;
  chapter_count?: number;
  [key: string]: unknown;
}

/** Quality report */
export interface QualityReport {
  chapters_written?: number;
  coverage_pct?: number;
  [key: string]: unknown;
}

/** Creator memory hit */
export interface MemoryHit {
  id?: string;
  content?: string;
  score?: number;
  source?: string;
  [key: string]: unknown;
}

/** Memory query result */
export interface MemoryQueryResult {
  hits?: MemoryHit[];
  results?: MemoryHit[];
  total?: number;
}

/** Paginated response */
export interface PaginatedResponse<T = unknown> {
  items?: T[];
  total?: number;
  page?: number;
  page_size?: number;
  has_more?: boolean;
}

/** Project/chapter info */
export interface ChapterInfo {
  id?: string | number;
  title?: string;
  chapter_no?: number;
  word_count?: number;
  status?: string;
  [key: string]: unknown;
}

/** Book/project info */
export interface ProjectInfo {
  slug?: string;
  name?: string;
  chapters?: ChapterInfo[];
  [key: string]: unknown;
}
