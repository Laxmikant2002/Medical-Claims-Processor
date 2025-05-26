from typing import Dict, Any, Optional
import redis.asyncio as redis
import json
import numpy as np
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from app.core.config import settings

class RedisService:
    def __init__(self, redis_url: str = None):
        """Initialize Redis service with either URL or cloud credentials."""
        if redis_url and redis_url.startswith("redis://"):
            # Local Docker connection
            self.redis = redis.from_url(redis_url)
        else:
            # Redis Cloud connection
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                username=settings.REDIS_USERNAME,
                password=settings.REDIS_PASSWORD,
            )
        self.is_initialized = False

    async def initialize(self):
        """Initialize the Redis service asynchronously."""
        if not self.is_initialized:
            await self._ensure_index()
            self.is_initialized = True

    async def _ensure_index(self):
        """Create search index if it doesn't exist."""
        try:
            # Define schema for document storage
            schema = (
                TextField("$.type", as_name="type"),
                TextField("$.filename", as_name="filename"),
                VectorField("$.embedding", 
                          "HNSW", {
                              "TYPE": "FLOAT32",
                              "DIM": settings.VECTOR_DIMENSION,
                              "DISTANCE_METRIC": settings.VECTOR_SIMILARITY_METRIC
                          }, as_name="embedding")
            )

            # Create index
            await self.redis.ft("doc_idx").create_index(
                schema,
                definition=IndexDefinition(
                    prefix=["doc:"],
                    index_type=IndexType.JSON
                )
            )
        except Exception as e:
            print(f"Index creation warning: {str(e)}")
            # Index might already exist
            pass

    async def test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            print(f"Redis connection error: {str(e)}")
            return False

    async def store_document(self, doc_id: str, doc_data: Dict[str, Any], embedding: np.ndarray) -> bool:
        """Store document data and its embedding."""
        try:
            # Prepare data for storage
            data = {
                "type": doc_data["type"],
                "filename": doc_data["filename"],
                "data": doc_data["data"],
                "embedding": embedding.tolist()
            }

            # Store in Redis
            await self.redis.json().set(f"doc:{doc_id}", "$", data)
            return True
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            return False

    async def search_similar_documents(self, query_embedding: np.ndarray, k: int = 5) -> list:
        """Search for similar documents using vector similarity."""
        try:
            # Prepare search query
            query = (
                f'*=>[KNN {k} @embedding $embedding AS score]'
            )
            
            # Execute search
            results = await self.redis.ft("doc_idx").search(
                query,
                query_params={
                    "embedding": query_embedding.tobytes()
                }
            )

            # Process results
            docs = []
            for doc in results.docs:
                data = json.loads(doc.json)
                data["score"] = doc.score
                docs.append(data)

            return docs
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID."""
        try:
            data = await self.redis.json().get(f"doc:{doc_id}")
            return data
        except Exception:
            return None

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID."""
        try:
            await self.redis.delete(f"doc:{doc_id}")
            return True
        except Exception:
            return False 