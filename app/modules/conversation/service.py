from app.modules.shared.logging import log_error, log_request, log_response
from app.modules.shared.sessions import get_session
from app.modules.shared.text_assistant import chat_text
from app.modules.shared.llm_assistant import assistant
from app.modules.shared.rag import get_retriever
from app.modules.shared.rag.semantic_cache import semantic_cache

from .models import ChatMetadata, ChatRequest, ChatResponse


class ConversationService:
    async def handle_chat(self, request: ChatRequest, *, language: str) -> ChatResponse:
        if not request.message or not request.message.strip():
            raise ValueError("Message must not be empty")

        session = get_session(request.session_id)

        log_request(
            module="conversation",
            session_id=session.id,
            extra={"language": language, "message_preview": request.message[:50]},
        )

        try:
            # 1. Cross-Lingual RAG: Translate to English to standardize the query
            query_en = request.message
            if language != "en":
                query_en = await assistant.translate_to_english(request.message)
            
            base_reply_en = ""
            rag_docs = []
            is_cache_hit = False

            # 2. Check Semantic Cache
            cached_reply = semantic_cache.get_cached_response(query_en)
            
            if cached_reply:
                base_reply_en = cached_reply
                is_cache_hit = True
                # Note: Cached answers lose original source docs metadata in this simple impl
            else:
                # 3. Retrieve & Generate (Force English generation to fill cache)
                retriever = get_retriever()
                rag_results = retriever.retrieve(query_en, top_k=5)
                rag_docs = [r.source_url for r in rag_results]

                context = {
                    "retrieved_chunks": [r.text for r in rag_results],
                    "source_docs": rag_docs,
                }

                # Force language="en" so we get a reusable English master answer
                result = await chat_text(
                    session=session,
                    language="en", 
                    message=query_en,
                    context=context,
                )
                base_reply_en = result["reply"]
                
                # Store in semantic cache (skip caching if the LLM failed)
                if not result.get("llm_error"):
                    semantic_cache.cache_response(query_en, base_reply_en)

            # 4. Final Translation to User's Language
            final_reply = base_reply_en
            if language != "en":
                final_reply = await assistant.translate_text(base_reply_en, language)

        except Exception as exc:  # noqa: BLE001
            log_error(module="conversation", session_id=session.id, error=exc)
            raise

        metadata = ChatMetadata(
            model=assistant.get_model_name(),
            latencyMs=0,
            sourceDocs=rag_docs if 'rag_docs' in locals() else None,
        )

        response = ChatResponse(
            reply=final_reply,
            language=language,
            metadata=metadata,
        )

        log_response(
            module="conversation",
            session_id=session.id,
            extra={"cached": is_cache_hit},
        )

        return response
