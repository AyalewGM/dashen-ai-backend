from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .loader import RawDocument, load_bank_public_pages, load_dashen_public_pages


load_dotenv(dotenv_path=Path(__file__).resolve().parents[4] / ".env", override=True)

DATA_DIR = Path(os.getenv("DASHEN_RAG_DATA_DIR", "data/rag"))


_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_OPENAI_EMBED_MODEL_NAME = os.getenv("OPENAI_EMBED_MODEL_NAME", "text-embedding-3-small")


def _get_embeddings() -> OpenAIEmbeddings:
    """Create and return OpenAI embeddings client."""
    if not _OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI embeddings are not configured. Set OPENAI_API_KEY environment variable."
        )
    return OpenAIEmbeddings(
        model=_OPENAI_EMBED_MODEL_NAME,
        api_key=_OPENAI_API_KEY,
    )


@dataclass
class RetrievalResult:
    text: str
    source_url: str


class _BankVectorStore:
    """Bank-aware vector store that supports multiple banks in a single collection."""
    
    def __init__(self, bank_id: str = "dashen") -> None:
        self._embeddings = _get_embeddings()
        self._bank_id = bank_id
        self.persist_directory = str(DATA_DIR / "chroma_db")
        
        # Use a single collection with bank_id metadata for filtering
        self._vector_db = Chroma(
            collection_name="multi_bank_knowledge",
            embedding_function=self._embeddings,
            persist_directory=self.persist_directory,
        )
        
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Ensure the bank's documents are indexed."""
        try:
            # Check if this bank has any documents
            results = self._vector_db.get(
                where={"bank_id": self._bank_id},
                limit=1
            )
            if not results or not results.get("ids"):
                self._build_index()
        except Exception:
            # If any error, try building
            self._build_index()

    def _build_index(self) -> None:
        """Build index for this specific bank."""
        # Ensure parent directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        print(f"DEBUG: Loading documents for bank '{self._bank_id}'...")
        raw_docs: list[RawDocument] = load_bank_public_pages(bank_id=self._bank_id)
        
        if not raw_docs:
            print(f"WARNING: No documents loaded for bank '{self._bank_id}'. Using fallback.")
            return
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )

        lc_docs = []
        for doc in raw_docs:
            chunks = splitter.split_text(doc.text)
            for chunk in chunks:
                if chunk.strip():
                    # Add bank_id to metadata for filtering
                    lc_docs.append(Document(
                        page_content=chunk, 
                        metadata={
                            "source": doc.url,
                            "bank_id": self._bank_id
                        }
                    ))

        if lc_docs:
            print(f"DEBUG: Indexing {len(lc_docs)} chunks for bank '{self._bank_id}' into ChromaDB...")
            self._vector_db.add_documents(lc_docs)
            print(f"DEBUG: Indexing complete for bank '{self._bank_id}'.")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Retrieve documents filtered by bank_id."""
        # Similarity search with bank_id filter
        results = self._vector_db.similarity_search(
            query, 
            k=top_k,
            filter={"bank_id": self._bank_id}
        )
        
        return [
            RetrievalResult(
                text=doc.page_content,
                source_url=doc.metadata.get("source", "")
            )
            for doc in results
        ]


# No-op retriever used when no embedding API key is configured
class _NoOpRetriever:
    """A no-op retriever that returns empty results."""
    
    def __init__(self, bank_id: str = "dashen") -> None:
        self._bank_id = bank_id
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        print(f"INFO: RAG disabled for bank '{self._bank_id}' - no embedding API key configured")
        return []


# Cache stores per bank to avoid re-indexing
_stores: dict[str, _BankVectorStore] = {}


def get_retriever(bank_id: str = "dashen") -> _BankVectorStore | _NoOpRetriever:
    """Get or create a bank-specific vector store retriever.
    
    Falls back to a no-op retriever if no embedding API key is configured.
    
    Args:
        bank_id: Bank identifier (dashen, abyssinia, awash, cbe)
    
    Returns:
        Bank-specific retriever instance or no-op retriever
    """
    if not _OPENAI_API_KEY:
        return _NoOpRetriever(bank_id=bank_id)
    
    global _stores
    if bank_id not in _stores:
        _stores[bank_id] = _BankVectorStore(bank_id=bank_id)
    return _stores[bank_id]
