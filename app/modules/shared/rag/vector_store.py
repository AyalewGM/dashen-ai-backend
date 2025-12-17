from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import google.generativeai as genai
from langchain_chroma import Chroma
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .loader import RawDocument, load_dashen_public_pages


DATA_DIR = Path(os.getenv("DASHEN_RAG_DATA_DIR", "data/rag"))


_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_GEMINI_EMBED_MODEL_NAME = os.getenv("GEMINI_EMBED_MODEL_NAME", "text-embedding-004")

if _GEMINI_API_KEY:
    genai.configure(api_key=_GEMINI_API_KEY)
else:
    pass


class GeminiEmbeddings(Embeddings):
    """Minimal embeddings helper compatible with the existing interface.

    Provides embed_documents and embed_query methods similar to LangChain
    embeddings classes so the rest of the vector store code can stay the same.
    """

    def __init__(self) -> None:
        if not _GEMINI_API_KEY:
            raise RuntimeError(
                "Gemini embeddings are not configured. Set GEMINI_API_KEY and GEMINI_EMBED_MODEL_NAME."
            )

    def _embed(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        # Call the module-level function directly
        # Note: 'models/' prefix is often safer
        model_name = _GEMINI_EMBED_MODEL_NAME
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        response = genai.embed_content(
            model=model_name,
            content=text,
            task_type=task_type,
        )
        return list(response["embedding"])

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t, task_type="retrieval_document") for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, task_type="retrieval_query")


@dataclass
class RetrievalResult:
    text: str
    source_url: str


class _DashenVectorStore:
    def __init__(self) -> None:
        self._embeddings = GeminiEmbeddings()
        self.persist_directory = str(DATA_DIR / "chroma_db")
        
        # Initialize ChromaDB
        self._vector_db = Chroma(
            collection_name="dashen_knowledge",
            embedding_function=self._embeddings,
            persist_directory=self.persist_directory,
        )
        
        self._ensure_index()

    def _ensure_index(self) -> None:
        # Check if collection is empty using getting count
        # Note: In newer Chroma versions we might need a different way, but this usually works
        try:
            # If the collection is empty, build it
            if self._vector_db._collection.count() == 0:
                self._build_index()
        except Exception:
            # If any error checking count, try building just in case
            self._build_index()

    def _build_index(self) -> None:
        # Ensure parent directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        raw_docs: list[RawDocument] = load_dashen_public_pages()
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
                    lc_docs.append(Document(page_content=chunk, metadata={"source": doc.url}))

        if lc_docs:
            print(f"DEBUG: Indexing {len(lc_docs)} chunks into ChromaDB...")
            self._vector_db.add_documents(lc_docs)
            print("DEBUG: Indexing complete.")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        # Similarity search
        results = self._vector_db.similarity_search(query, k=top_k)
        
        return [
            RetrievalResult(
                text=doc.page_content,
                source_url=doc.metadata.get("source", "")
            )
            for doc in results
        ]


_store: _DashenVectorStore | None = None


def get_retriever() -> _DashenVectorStore:
    global _store
    if _store is None:
        _store = _DashenVectorStore()
    return _store
