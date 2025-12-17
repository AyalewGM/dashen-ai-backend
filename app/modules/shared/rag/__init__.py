"""RAG utilities for Dashen Bank assistant.

Provides high-level retrieval functions used by the conversation service.
"""

from .vector_store import get_retriever

__all__ = ["get_retriever"]
