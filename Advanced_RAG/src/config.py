import os
from dotenv import load_dotenv
load_dotenv()

# Base directory (project root)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API keys

PINECONE_API_KEY=os.getenv("PINECONE_API_KEY","")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")

# Chunking settings

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP:int = 200


# PineCone settings

PINECONE_INDEX_NAME: str = "advancedragindex"
PINECONE_NAMESPACE: str = "niths"
PINECONE_CLOUD: str = "aws"
PINECONE_REGION: str = "us-east-1"
PINECONE_EMBED_MODEL: str = "llama-text-embed-v2"  
PINECONE_RERANK_MODEL: str = "bge-reranker-v2-m3"

# Retrieval settings

TOP_K:int = 10
RERANK_TOP_N:int = 5

# Generation settings
PROJECT_ID = os.getenv("PROJECT_ID","")
LOCATION: str = "us-central1"
GEMINI_MODEL: str = "gemini-2.0-flash"
MAX_TOKENS: int = 1024
TEMPERATURE: float = 0.2

# Cache Settings

CACHE_BACKEND: str = os.getenv("CACHE_BACKEND", "redis")                         
CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
EXACT_CACHE_TTL: int = int(os.getenv("EXACT_CACHE_TTL", "604800"))                  # 7 days in seconds
SEMANTIC_CACHE_TTL: int = int(os.getenv("SEMANTIC_CACHE_TTL", "604800"))             # 7 days in seconds
SEMANTIC_CACHE_THRESHOLD: float = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.92"))
RETRIEVAL_CACHE_TTL: int = int(os.getenv("RETRIEVAL_CACHE_TTL", "86400"))            # 1 day in seconds
RETRIEVAL_CACHE_THRESHOLD: float = float(os.getenv("RETRIEVAL_CACHE_THRESHOLD", "0.85"))
DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "rag_cache.db"))
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")