from app.modules.shared.logging import log_error, log_request, log_response
from app.modules.shared.sessions import get_session
from app.modules.shared.text_assistant import chat_text
from app.modules.shared.llm_assistant import assistant
from app.modules.shared.rag import get_retriever
from app.modules.shared.rag.semantic_cache import semantic_cache
from app.modules.escalation import escalation_service
from app.modules.escalation.models import ConversationMessage

from .models import ChatMetadata, ChatRequest, ChatResponse
from .analytics_agent import analytics_agent


class ConversationService:
    async def handle_chat(self, request: ChatRequest, *, language: str, bank_id: str = "dashen") -> ChatResponse:
        if not request.message or not request.message.strip():
            raise ValueError("Message must not be empty")

        session = get_session(request.session_id)

        log_request(
            module="conversation",
            session_id=session.id,
            extra={"language": language, "message_preview": request.message[:50]},
        )

        try:
            # 1. Check if this is an analytics question
            if analytics_agent.is_analytics_question(request.message):
                # Route to analytics agent for data-driven answers
                analytics_reply = await analytics_agent.handle_analytics_query(
                    message=request.message,
                    bank_id=bank_id,
                    language=language
                )
                
                if analytics_reply:
                    metadata = ChatMetadata(
                        model="analytics-agent",
                        latencyMs=0,
                        sourceDocs=["Internal Analytics Database"],
                    )
                    
                    response = ChatResponse(
                        reply=analytics_reply,
                        language=language,
                        metadata=metadata,
                    )
                    
                    log_response(
                        module="conversation",
                        session_id=session.id,
                        extra={"analytics_query": True},
                    )
                    
                    return response
            
            # 2. Cross-Lingual RAG: Translate to English to standardize the query
            query_en = request.message
            if language != "en":
                query_en = await assistant.translate_to_english(request.message)
            
            base_reply_en = ""
            rag_docs = []
            is_cache_hit = False

            # 3. Check Semantic Cache
            cached_reply = semantic_cache.get_cached_response(query_en)
            
            if cached_reply:
                base_reply_en = cached_reply
                is_cache_hit = True
                # Note: Cached answers lose original source docs metadata in this simple impl
            else:
                # 3. Retrieve & Generate (Force English generation to fill cache)
                # Get bank-specific retriever
                retriever = get_retriever(bank_id=bank_id)
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
                    bank_id=bank_id,
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

        # Check if escalation is needed
        conversation_history = [
            ConversationMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp", ""),
                language=language
            )
            for msg in session.messages[-10:]  # Last 10 messages
        ]
        
        escalation_trigger = await escalation_service.detect_escalation_needed(
            conversation_history=conversation_history,
            language=language
        )
        
        # If escalation needed, override response
        if escalation_trigger.should_escalate:
            from app.modules.escalation.models import CreateEscalationRequest
            
            escalation_request = CreateEscalationRequest(
                session_id=session.id,
                bank_id=bank_id,
                reason=escalation_trigger.reason or "Customer needs human assistance",
                trigger_type=escalation_trigger.trigger_type,
                priority=escalation_trigger.priority,
                conversation_history=conversation_history,
                language=language
            )
            
            escalation_response = await escalation_service.create_escalation(escalation_request)
            final_reply = escalation_response.message
        
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
            extra={"cached": is_cache_hit, "escalated": escalation_trigger.should_escalate if 'escalation_trigger' in locals() else False},
        )

        return response
