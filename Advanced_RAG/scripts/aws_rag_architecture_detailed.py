"""
AWS architecture diagram for Advanced RAG (from Project_Architecture_Detailed.doc).

Shows clearly:
- User can UPLOAD document (save → extract → chunk → upsert to Pinecone + metadata).
- User can QUERY uploaded document: backend checks CACHE first; on CACHE MISS,
  retrieval from Pinecone with RERANKING, then Gemini generates answer.
- Frontend: TypeScript (React + Vite), Dashboard, api.ts, Sidebar, ChatWindow, RetrievalPanel.

Requires: pip install diagrams, GraphViz on PATH.
Run: uv run python scripts/aws_rag_architecture_detailed.py
Output: advanced_rag_aws_architecture_detailed.png
"""

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECS
from diagrams.aws.database import ElasticacheForRedis
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.storage import S3
from diagrams.gcp.ml import VertexAI
from diagrams.onprem.client import User
from diagrams.onprem.database import Qdrant

OUTPUT_DIR = Path(__file__).resolve().parents[1]
FILENAME = "advanced_rag_aws_architecture_detailed"


def main():
    with Diagram(
        "Advanced RAG - AWS Architecture (Project_Architecture_Detailed)",
        filename=str(OUTPUT_DIR / FILENAME),
        show=False,
        direction="TB",
    ):
        user = User("User")

        # Frontend: TypeScript (React + Vite) per doc — upload docs, query, cache metrics
        with Cluster("Frontend (TypeScript — React + Vite)"):
            cdn = CloudFront("CloudFront")
            static = S3("S3\nStatic assets\nDashboard, Sidebar,\nChatWindow, RetrievalPanel\napi.ts: POST /ingest, POST /chat")

        with Cluster("API Layer"):
            api_gw = APIGateway("API Gateway")

        with Cluster("FastAPI Backend (src/main.py)"):
            backend = ECS("Orchestration\nIngestion + Chat + Cache tiers")

        with Cluster("Cache — Check First on Query"):
            redis = ElasticacheForRedis("ElastiCache Redis\nTier 1 exact → Tier 2 semantic\n→ Tier 3 retrieval\n(doc_version invalidation)")

        with Cluster("Vector Store — Retrieval + Rerank (on cache miss)"):
            pinecone = Qdrant("Pinecone\nindex + namespace\nembed + rerank\n(reranking.py)")

        with Cluster("Document Storage"):
            uploads_s3 = S3("S3\ndata/uploads\n(uuid)_filename")

        with Cluster("LLM — Answer Generation"):
            vertex = VertexAI("Vertex AI\nGemini 2.0 Flash")

        # User → Frontend (upload doc + query doc)
        user >> Edge(label="Upload document\nor Query document") >> cdn
        cdn >> static
        cdn >> api_gw >> backend

        # ——— UPLOAD FLOW ———
        backend >> Edge(label="Upload: save file") >> uploads_s3
        backend >> Edge(label="Upload: chunk + upsert") >> pinecone
        # ——— QUERY FLOW: check cache first, on miss → Pinecone retrieval + reranking ———
        backend >> Edge(label="Query: 1. Check cache") >> redis
        backend >> Edge(label="On cache miss:\nRetrieve and rerank") >> pinecone
        pinecone >> Edge(label="Context chunks") >> backend
        backend >> Edge(label="Generate answer") >> vertex

    print(f"Diagram saved to: {OUTPUT_DIR / FILENAME}.png")


if __name__ == "__main__":
    main()
