from typing import Any, Optional

import asyncio
import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .bank_config import get_bank_config
from .config import config
from .sessions import Session

logger = logging.getLogger(__name__)

# ትሑት (Tihut) - Multilingual Banking AI Assistant
# "Respectful. Intelligent. Always Ready to Assist."
# Powered by Goozam Technologies

LANGUAGE_SYSTEM_PROMPTS: dict[str, str] = {
    "en": (
        "You are ትሑት (Tihut), a respectful and intelligent banking AI assistant. "
        "Answer concisely in professional English. "
        "Use the provided context to answer the user's question accurately. "
        "Be helpful, clear, and trustworthy."
    ),
    "am": (
        "አንተ ትሑት ነህ፣ ማክበርና ብልህ የባንክ AI ረዳት። "
        "የተሰጠውን የእንግሊዝኛ መረጃ አንብብ፣ ነገር ግን የተጠቃሚውን ጥያቄ በስሩ፣ በሰዋስው ትክክለኛ እና በመደበኛ አማርኛ መልስ። "
        "ቃል በቃል አትተርጉም፤ ተፈጥሯዊ የአማርኛ አገላለጽ እና ትክክለኛ የባንክ ቃላትን ተጠቀም። "
        "ስሜት፡ ጨዋ፣ ረዳት እና ማክበር።"
    ),
    "om": (
        "Ati ትሑት (Tihut) dha, gargaaraa baankii AI kabajamaa fi beekamaa. "
        "Odeeffannoo Afaan Ingiliffaan dhiyaate fayyadamuun, gaaffii maamilaa Afaan Oromoo qulqulluu, "
        "sirrii, fi kabaja qabuun deebisi. Afaan Ingiliffa, Afaan Amharaa ykn Afaan biraa hin dabaliin. "
        "Jechoota Baankii sirrii ta'an fayyadami. Deebii kennuuf yeroo hunda karaalee fayyadamuu "
        "baankichaa ibsi (CBE Birr, mobile app, ATM, filannoo, oomishaloota gara biyya alaa). "
        "Gargaaraa, ifa, fi amanamaa ta'i."
    ),
    "ti": (
        "You are ትሑት (Tihut), a respectful and intelligent banking AI assistant. "
        "Read the English context and answer in fluent, formal Tigrinya. "
        "Ensure the grammar is correct and the tone is respectful. "
        "Use proper banking terms in Tigrinya. Be helpful and trustworthy."
    ),
    "so": (
        "You are ትሑት (Tihut), a respectful and intelligent banking AI assistant. "
        "Read the English context and answer in fluent, formal Somali. "
        "Ensure the grammar is correct and the tone is respectful. "
        "Use proper banking terms in Somali. Be helpful and trustworthy."
    ),
    "sid": (
        "You are ትሑት (Tihut), a respectful and intelligent banking AI assistant. "
        "Read the English context and answer in fluent, formal Sidama (Sidaamu Afoo). "
        "Ensure the grammar is correct and the tone is respectful. "
        "Use proper banking terms in Sidama. Be helpful and trustworthy."
    ),
}


load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")
_GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))


if _GEMINI_API_KEY:
    _genai_client = genai.Client(
        api_key=_GEMINI_API_KEY,
        http_options=types.HttpOptions(api_version="v1"),
    )
else:
    _genai_client = None



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
        bank_id: str = "dashen",
    ) -> dict[str, Any]:
        start = time.monotonic()

        bank_config = get_bank_config(bank_id)
        system_prompt = LANGUAGE_SYSTEM_PROMPTS.get(language, LANGUAGE_SYSTEM_PROMPTS["en"])
        
        # Replace generic "Dashen Bank" with actual bank name
        system_prompt = system_prompt.replace("Dashen Bank", bank_config.bank_name)

        # If RAG context is provided, append it to the system prompt so the
        # model can ground its answers in Dashen Bank-specific information.
        retrieved_chunks = None
        if context is not None:
            retrieved_chunks = context.get("retrieved_chunks")

        if retrieved_chunks:
            rag_context = "\n\n".join(retrieved_chunks)
            system_prompt = (
                f"{system_prompt}\n\n"
                f"You are {bank_config.bank_name}'s virtual concierge and customer support assistant.\n"
                f"{bank_config.chatbot_context}\n\n"
                "\nYour role and behavior:\n"
                f"- Act as a knowledgeable, trustworthy {bank_config.bank_name} representative.\n"
                "- Communicate clearly, politely, and concisely.\n"
                "- Use simple language and avoid jargon unless it is necessary.\n"
                "\nGrounding and sources:\n"
                f"- Use ONLY the following {bank_config.bank_name} information as your primary source of truth.\n"
                "- If the answer is not clearly covered in this information:\n"
                "  - Say that you do not know or that the information is not available.\n"
                f"  - Encourage the customer to contact official {bank_config.bank_name} channels (such as branches, call center, or the official website) for confirmation.\n"
                "\nSafety and scope:\n"
                "- Do NOT invent fees, rates, or product details.\n"
                "- Do NOT give legal, tax, or investment advice.\n"
                "- When you are unsure, be transparent about your uncertainty.\n\n"
                f"{bank_config.bank_name} reference information:\n"
                f"{rag_context}"
            )

        # Fallback stub reply if Gemini is not configured
        if _genai_client is None:
            reply = "I’m not configured with an AI model right now. Please try again later."
            llm_error = True
        else:
            try:
                prompt = f"{system_prompt}\n\nUser: {message}"

                # Use the new google-genai async API
                response = await _genai_client.aio.models.generate_content(
                    model=_GEMINI_MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=_GEMINI_TEMPERATURE),
                )
                reply = response.text or ""
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
            "model": _GEMINI_MODEL_NAME if _genai_client is not None else config.default_model_name,
            "latency_ms": elapsed_ms,
            "source_docs": source_docs,
            "llm_error": llm_error,
        }

    async def translate_to_english(self, text: str) -> str:
        """Translates text to English for RAG retrieval purposes."""
        if _genai_client is None:
            return text

        try:
            prompt = (
                "Translate the following text to English. "
                "Output ONLY the translation, nothing else.\n\n"
                f"Text: {text}"
            )
            response = await _genai_client.aio.models.generate_content(
                model=_GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0),
            )
            return (response.text or "").strip() or text
        except Exception:
            return text

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translates text to the target language code (e.g., 'am', 'om', 'ti')."""
        if _genai_client is None or target_lang == "en":
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
            response = await _genai_client.aio.models.generate_content(
                model=_GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0),
            )
            return (response.text or "").strip() or text
        except Exception:
            return text


    def get_model_name(self) -> str:
        return _GEMINI_MODEL_NAME or "gemini-unknown"

assistant = LlmAssistant()
llm_assistant = assistant
