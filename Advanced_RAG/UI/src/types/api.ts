export type ChunkingStrategy = "parent_child" | "sentence_window";
export type SessionStatus = "IDLE" | "PROCESSING";

export interface UploadedDocument {
  file_name: string;
  file_path: string;
  uploaded_at: string;
}

export interface DocumentsResponse {
  total_documents: number;
  documents: UploadedDocument[];
}

export interface IngestResponse {
  file: string;
  strategy: ChunkingStrategy;
  chunks: number;
  message: string;
}

export interface SourceChunk {
  id: string;
  source: string;
  chunk_text: string;
  page: number | string | null;
  score: number;
  method: string;
  parent_id: string;
}

export interface ChatResponse {
  answer: string;
  strategy: ChunkingStrategy;
  file_name: string;
  file_path: string;
  chunk_count: number;
  contexts: SourceChunk[];
  cache_hit: boolean;
  cache_tier: string | null;
  response_time_ms: number | null;
}

export interface CacheStatsResponse {
  [key: string]: unknown;
}

