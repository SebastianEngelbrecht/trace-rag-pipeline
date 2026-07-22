export interface UiChunk {
  content: string;
  source_url: string;
  chunk_index: number;
  rank_score?: number;
}

export interface GenerationResponse {
  answer: string;
  chunks: UiChunk[];
  prompt: string;
  response_time_ms?: number;
  tokens_used?: number;
  retrieval_time_ms?: number;
}

export interface IngestionConfig {
  url: string;
  chunk_size?: number;
  overlap?: number;
  max_depth?: number;
}

export interface WsMessage {
  status: 'running' | 'complete' | 'error';
  message: string;
}
