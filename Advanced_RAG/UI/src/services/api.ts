import axios from "axios";
import type {
  CacheStatsResponse,
  ChatResponse,
  ChunkingStrategy,
  DocumentsResponse,
  IngestResponse
} from "../types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
  timeout: 30000
});

export async function ingestFile(params: {
  file: File;
  username: string;
  chunkingStrategy: ChunkingStrategy;
}): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", params.file);
  form.append("namespace", params.username);
  form.append("username", params.username);
  form.append("chunking_strategy", params.chunkingStrategy);

  const response = await api.post<IngestResponse>("/ingest", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

export async function listDocuments(username: string): Promise<DocumentsResponse> {
  const response = await api.get<DocumentsResponse>("/documents", {
    params: { username }
  });
  return response.data;
}

export async function chat(params: {
  username: string;
  question: string;
  filePath: string;
  chunkingStrategy: ChunkingStrategy;
}): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/chat", {
    username: params.username,
    question: params.question,
    query: params.question,
    file_path: params.filePath,
    chunking_strategy: params.chunkingStrategy
  });
  return response.data;
}

export async function getCacheStats(username: string): Promise<CacheStatsResponse> {
  const response = await api.get<CacheStatsResponse>("/cache/stats", {
    params: { username }
  });
  return response.data;
}

export async function clearCache(username: string): Promise<unknown> {
  const response = await api.post("/cache/clear", { username });
  return response.data;
}

export async function clearVectorSpace(username: string): Promise<unknown> {
  const response = await api.delete("/vectors", { data: { username } });
  return response.data;
}

export async function clearDocuments(username: string, filenames: string[]): Promise<void> {
  await Promise.all(
    filenames.map((filename) =>
      api.delete(`/documents/${encodeURIComponent(filename)}`, {
        data: { username }
      })
    )
  );
}

export default api;

