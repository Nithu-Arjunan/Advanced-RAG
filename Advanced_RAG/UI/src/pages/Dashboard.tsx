import { useEffect, useMemo, useState } from "react";
import ChatWindow from "../components/ChatWindow";
import DebugFooter from "../components/DebugFooter";
import RetrievalPanel from "../components/RetrievalPanel";
import Sidebar from "../components/Sidebar";
import TopHeader from "../components/TopHeader";
import {
  chat,
  clearCache,
  clearDocuments,
  clearVectorSpace,
  getCacheStats,
  ingestFile,
  listDocuments
} from "../services/api";
import type {
  ChatResponse,
  ChunkingStrategy,
  IngestResponse,
  SessionStatus,
  SourceChunk,
  UploadedDocument
} from "../types/api";

interface UIMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  cacheHit?: boolean;
  cacheTier?: string | null;
  latencyMs?: number | null;
}

export default function Dashboard() {
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<SessionStatus>("IDLE");
  const [chunkingStrategy, setChunkingStrategy] = useState<ChunkingStrategy>("parent_child");
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<UploadedDocument | undefined>();
  const [ingestionResult, setIngestionResult] = useState<IngestResponse | null>(null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [retrievedChunks, setRetrievedChunks] = useState<SourceChunk[]>([]);
  const [cacheTier, setCacheTier] = useState("MISS");
  const [responseTimeMs, setResponseTimeMs] = useState<number | null>(null);
  const [embeddingModel] = useState("all-MiniLM-L6-v2");
  const [cacheStats, setCacheStats] = useState<unknown | null>(null);

  const processing = status === "PROCESSING";

  const latestMetrics = useMemo(
    () => ({
      cacheTier,
      embeddingModel,
      chunksRetrieved: retrievedChunks.length,
      responseTimeMs
    }),
    [cacheTier, embeddingModel, retrievedChunks.length, responseTimeMs]
  );

  const ensureUsername = () => {
    if (!username.trim()) {
      throw new Error("Please enter a username first.");
    }
  };

  const refreshDocuments = async () => {
    ensureUsername();
    const response = await listDocuments(username.trim());
    setDocuments(response.documents);
    if (!selectedDocument && response.documents.length > 0) {
      setSelectedDocument(response.documents[0]);
    }
  };

  const runWithStatus = async <T,>(task: () => Promise<T>): Promise<T> => {
    setStatus("PROCESSING");
    try {
      return await task();
    } finally {
      setStatus("IDLE");
    }
  };

  const handleUpload = async (file: File) => {
    await runWithStatus(async () => {
      ensureUsername();
      const result = await ingestFile({
        file,
        username: username.trim(),
        chunkingStrategy
      });
      setIngestionResult(result);
      await refreshDocuments();
    });
  };

  const handleAsk = async (question: string) => {
    await runWithStatus(async () => {
      ensureUsername();
      if (!selectedDocument) throw new Error("Select a document before chatting.");

      setMessages((prev) => [...prev, { role: "user", content: question }]);
      const response: ChatResponse = await chat({
        username: username.trim(),
        question,
        filePath: selectedDocument.file_path,
        chunkingStrategy
      });

      setRetrievedChunks(response.contexts ?? []);
      setCacheTier(response.cache_hit ? (response.cache_tier ?? "exact").toUpperCase() : "MISS");
      setResponseTimeMs(response.response_time_ms ?? null);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: response.contexts,
          cacheHit: response.cache_hit,
          cacheTier: response.cache_tier,
          latencyMs: response.response_time_ms
        }
      ]);
    });
  };

  const handleCacheStatus = async () => {
    await runWithStatus(async () => {
      ensureUsername();
      const stats = await getCacheStats(username.trim());
      setCacheStats(stats);
    });
  };

  const handleClearCache = async () => {
    await runWithStatus(async () => {
      ensureUsername();
      await clearCache(username.trim());
      setCacheTier("MISS");
      setCacheStats(null);
    });
  };

  const handleClearVectorSpace = async () => {
    await runWithStatus(async () => {
      ensureUsername();
      await clearVectorSpace(username.trim());
      setDocuments([]);
      setSelectedDocument(undefined);
      setRetrievedChunks([]);
      setCacheStats(null);
    });
  };

  const handleClearDocuments = async () => {
    await runWithStatus(async () => {
      ensureUsername();
      if (documents.length === 0) return;
      await clearDocuments(
        username.trim(),
        documents.map((doc) => doc.file_name)
      );
      setDocuments([]);
      setSelectedDocument(undefined);
    });
  };

  useEffect(() => {
    if (!username.trim()) {
      setDocuments([]);
      setSelectedDocument(undefined);
      return;
    }
    void refreshDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  const handleSourceClick = (source: SourceChunk) => {
    const matchingDoc = documents.find((doc) => doc.file_name === source.source);
    if (matchingDoc) setSelectedDocument(matchingDoc);
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-[1700px] flex-col gap-4 p-4">
      <TopHeader username={username} onUsernameChange={setUsername} status={status} />

      <section className="grid gap-4 lg:grid-cols-[320px_1fr_380px]">
        <Sidebar
          username={username}
          chunkingStrategy={chunkingStrategy}
          onStrategyChange={setChunkingStrategy}
          onUpload={handleUpload}
          ingestionResult={ingestionResult}
          documents={documents}
          selectedDocument={selectedDocument}
          onSelectDocument={setSelectedDocument}
          onRefreshDocuments={refreshDocuments}
          onCacheStatus={handleCacheStatus}
          onClearCache={handleClearCache}
          onClearVectorSpace={handleClearVectorSpace}
          onClearDocuments={handleClearDocuments}
          cacheStats={cacheStats}
          processing={processing}
        />
        <ChatWindow
          messages={messages}
          processing={processing}
          onSend={handleAsk}
          onSourceClick={handleSourceClick}
        />
        <RetrievalPanel chunks={retrievedChunks} />
      </section>

      <DebugFooter
        cacheTier={latestMetrics.cacheTier}
        embeddingModel={latestMetrics.embeddingModel}
        chunksRetrieved={latestMetrics.chunksRetrieved}
        responseTimeMs={latestMetrics.responseTimeMs}
      />
    </main>
  );
}
