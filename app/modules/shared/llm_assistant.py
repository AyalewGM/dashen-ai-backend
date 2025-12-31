from typing import Any, Optional

import asyncio
import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv
import google.generativeai as genai

from .config import config
from .sessions import Session

logger = logging.getLogger(__name__)

LANGUAGE_SYSTEM_PROMPTS: dict[str, str] = {
    "en": (
        "You are Dashen Bank's virtual concierge. Answer concisely in professional English. "
        "Use the provided context to answer the user's question accurately."
    ),
    "am": (
        "You are Dashen Bank's professional customer support agent. "
        "Read the provided English context, but answer the user's question in fluent, grammatically correct, and formal Amharic. "
        "Do not translate word-for-word; use natural Amharic phrasing and proper banking terminology. "
        "Tone: Polite, helpful, and respectful."
    ),
    "om": (
        "Ati ogeessa deeggarsa maamilaa Baankii Daashenidha. "
        "Odeeffannoo Afaan Ingiliffaan dhiyaate fayyadamuun, gaaffii maamilaa Afaan Oromoo qulqulluu, "
        "sirrii, fi kabaja qabuun deebisi. Jechoota Baankii sirrii ta'an fayyadami."
    ),
    "ti": (
        "You are Dashen Bank's support agent. Read the English context and answer in fluent, formal Tigrinya. "
        "Ensure the grammar is correct and the tone is respectful. Use proper banking terms in Tigrinya."
    ),
    "so": (
        "You are Dashen Bank's support agent. Read the English context and answer in fluent, formal Somali. "
        "Ensure the grammar is correct and the tone is respectful. Use proper banking terms in Somali."
    ),
    "sid": (
        "You are Dashen Bank's support agent. Read the English context and answer in fluent, formal Sidama (Sidaamu Afoo). "
        "Ensure the grammar is correct and the tone is respectful. Use proper banking terms in Sidama."
    ),
}


load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env", override=True)

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")
_GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))


if _GEMINI_API_KEY:
    genai.configure(api_key=_GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel(_GEMINI_MODEL_NAME)
else:
    _gemini_model = None



class LlmAssistant:
    """Abstraction over the underlying AI model.

    In a real system this would call OpenAI, Azure, local models, etc.
    Here we just simulate a reply while enforcing language control.
    """

    async def generate_reply(
        self,
        *,
        session: Session,
        language: str,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        start = time.monotonic()

        system_prompt = LANGUAGE_SYSTEM_PROMPTS.get(language, LANGUAGE_SYSTEM_PROMPTS["en"])

        # If RAG context is provided, append it to the system prompt so the
        # model can ground its answers in Dashen Bank-specific information.
        retrieved_chunks = None
        if context is not None:
            retrieved_chunks = context.get("retrieved_chunks")

        if retrieved_chunks:
            rag_context = "\n\n".join(retrieved_chunks)
            system_prompt = (
                f"{system_prompt}\n\n"
                "You are Dashen Bank's virtual concierge and customer support assistant.\n"
                "\nYour role and behavior:\n"
                "- Act as a knowledgeable, trustworthy Dashen Bank representative.\n"
                "- Communicate clearly, politely, and concisely.\n"
                "- Use simple language and avoid jargon unless it is necessary.\n"
                "\nGrounding and sources:\n"
                "- Use ONLY the following Dashen Bank information as your primary source of truth.\n"
                "- If the answer is not clearly covered in this information:\n"
                "  - Say that you do not know or that the information is not available.\n"
                "  - Encourage the customer to contact official Dashen Bank channels (such as branches, call center, or the official website) for confirmation.\n"
                "\nSafety and scope:\n"
                "- Do NOT invent fees, rates, or product details.\n"
                "- Do NOT give legal, tax, or investment advice.\n"
                "- When you are unsure, be transparent about your uncertainty.\n\n"
                "Dashen Bank reference information:\n"
                f"{rag_context}"
            )

        # Fallback stub reply if Gemini is not configured
        if _gemini_model is None:
            reply = "I’m not configured with an AI model right now. Please try again later."
            llm_error = True
        else:
            try:
                prompt = f"{system_prompt}\n\nUser: {message}"

                # google-generativeai is synchronous; run in a thread to
                # avoid blocking the event loop.
                response = await asyncio.to_thread(
                    _gemini_model.generate_content,
                    prompt,
                    generation_config={"temperature": _GEMINI_TEMPERATURE},
                )
                reply = getattr(response, "text", None) or ""
                llm_error = False
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Gemini generate_content failed (model=%s, configured=%s): %s",
                    _GEMINI_MODEL_NAME,
                    bool(_GEMINI_API_KEY),
                    exc,
                )
                reply = "I’m having trouble generating a response right now. Please try again."
                llm_error = True

        elapsed_ms = int((time.monotonic() - start) * 1000)
        source_docs: Optional[list[str]] = None
        if context and "source_docs" in context:
            source_docs = context["source_docs"]

        return {
            "reply": reply,
            "language": language,
            "model": _GEMINI_MODEL_NAME if _gemini_model is not None else config.default_model_name,
            "latency_ms": elapsed_ms,
            "source_docs": source_docs,
            "llm_error": llm_error,
        }

    async def translate_to_english(self, text: str) -> str:
        """Translates text to English for RAG retrieval purposes."""
        if _gemini_model is None:
            return text

        try:
            prompt = (
                "Translate the following text to English. "
                "Output ONLY the translation, nothing else.\n\n"
                f"Text: {text}"
            )
            response = await asyncio.to_thread(
                _gemini_model.generate_content,
                prompt,
                generation_config={"temperature": 0.0},
            )
            return getattr(response, "text", "").strip() or text
        except Exception:
            return text

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translates text to the target language code (e.g., 'am', 'om', 'ti')."""
        if _gemini_model is None or target_lang == "en":
            return text

        lang_map = {
            "am": "Amharic",
            "om": "Afan Oromo",
            "ti": "Tigrinya",
            "so": "Somali",
        }
        target_name = lang_map.get(target_lang, target_lang)

        try:
            prompt = (
                f"Translate the following text to {target_name}. "
                "Output ONLY the translation, nothing else. "
                "Maintain the professional tone.\n\n"
                f"Text: {text}"
            )
            response = await asyncio.to_thread(
                _gemini_model.generate_content,
                prompt,
                generation_config={"temperature": 0.0},
            )
            return getattr(response, "text", "").strip() or text
        except Exception:
            return text


    def get_model_name(self) -> str:
        return _GEMINI_MODEL_NAME or "gemini-unknown"

assistant = LlmAssistant()
