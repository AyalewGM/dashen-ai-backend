from __future__ import annotations

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .vector_store import _get_embeddings

DATA_DIR = Path(os.getenv("DASHEN_RAG_DATA_DIR", "data/rag"))
CACHE_DIR = DATA_DIR / "chroma_cache"


class SemanticCache:
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self._enabled = bool(os.getenv("OPENAI_API_KEY"))
        
        if not self._enabled:
            print("INFO: Semantic cache disabled - OPENAI_API_KEY not set")
            return
        
        self.embeddings = _get_embeddings()
        
        # Initialize separate Chroma collection for caching
        self.vector_db = Chroma(
            collection_name="response_cache",
            embedding_function=self.embeddings,
            persist_directory=str(CACHE_DIR),
        )

    def get_cached_response(self, query: str) -> str | None:
        """Looks for a semantically similar query in the cache."""
        if not self._enabled:
            return None
        
        try:
            # Check if cache is empty first to avoid errors
            # (Chroma might throw if collection is empty or doesn't exist yet)
            # A simple way is to try searching.
            results = self.vector_db.similarity_search_with_score(query, k=1)
        except Exception:
            return None

        if not results:
            return None

        doc, score = results[0]
        
        # Chroma score is distance (lower is better) or similarity?
        # LangChain Chroma uses L2 distance by default (lower is better), 
        # or Cosine distance (lower is better, 0=identical, 1=opposite).
        # Wait, langchain-chroma defaults: 
        # If using cosine distance, score ranges from 0 to 2.
        # Actually, let's assume cosine similarity if configured, or just inspect.
        # Standard Chroma default is L2. 
        # Let's verify behavior. If score is distance, we want score < (1 - threshold).
        
        # Let's stick to a safe heuristic: if we see very low distance (e.g. < 0.2), it's a hit.
        # 0.2 distance roughly corresponds to very high similarity.
        
        print(f"DEBUG: Cache lookup score (distance): {score}")
        
        if score < 0.25:  # Tunable threshold for L2/Cosine distance
            print(f"DEBUG: Semantic Cache HIT! (Distance: {score})")
            return doc.metadata.get("response")
            
        print(f"DEBUG: Semantic Cache MISS (Distance: {score} > 0.25)")
        return None

    def cache_response(self, query: str, response: str) -> None:
        """Stores a query-response pair in the semantic cache."""
        if not self._enabled:
            return
        
        doc = Document(
            page_content=query,
            metadata={"response": response}
        )
        self.vector_db.add_documents([doc])
        print("DEBUG: Response cached semantically.")


# Singleton instance
semantic_cache = SemanticCache()
