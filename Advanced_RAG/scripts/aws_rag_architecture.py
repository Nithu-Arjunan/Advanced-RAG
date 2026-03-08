"""
Generate AWS-style architecture diagram for Advanced_RAG.

Requires: pip install diagrams  and  GraphViz installed on your system.
Run: uv run python scripts/aws_rag_architecture.py
     or: python scripts/aws_rag_architecture.py

Output: advanced_rag_aws_architecture.png in the project root.
"""

from pathlib import Path

from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import ElasticacheForRedis
from diagrams.aws.network import ALB, APIGateway, CloudFront
from diagrams.aws.storage import S3
from diagrams.gcp.ml import VertexAI
from diagrams.onprem.client import User
from diagrams.onprem.database import Qdrant

# Output next to script's parent (project root)
OUTPUT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = OUTPUT_DIR / "advanced_rag_aws_architecture.png"


def main():
    with Diagram(
        "Advanced RAG - AWS Architecture",
        filename=str(OUTPUT_DIR / OUTPUT_FILE.stem),
        show=False,
        direction="TB",
    ):
        user = User("End User")

        with Cluster("Frontend"):
            cdn = CloudFront("CloudFront\n(CDN)")
            static = S3("S3\nReact + Vite UI")

        with Cluster("API Layer"):
            api_gw = APIGateway("API Gateway")
            alb = ALB("ALB")
            backend = ECS("ECS / Fargate\nFastAPI\n(ingest, chat, cache)")

        with Cluster("Caching"):
            redis = ElasticacheForRedis("ElastiCache\nRedis\n(multi-tier cache)")

        with Cluster("Vector Store"):
            pinecone = Qdrant("Pinecone\n(Vector Index\n+ Reranker)")

        with Cluster("Document Storage"):
            docs_s3 = S3("S3\nUploaded Documents")

        with Cluster("LLM"):
            vertex = VertexAI("Vertex AI\nGemini 2.0 Flash")

        # Flows
        user >> cdn >> static
        user >> cdn >> api_gw >> alb >> backend

        backend >> redis
        backend >> pinecone
        backend >> docs_s3
        backend >> vertex

    print(f"Diagram saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
