from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request, status


_ALLOWED = {"am", "om", "ti", "en"}


def _validate(lang: str) -> str:
    lang = lang.strip().lower()
    if lang not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Allowed: {', '.join(sorted(_ALLOWED))}",
        )
    return lang


async def resolve_language(request: Request) -> str:
    header_lang = request.headers.get("X-Language")
    if header_lang:
        return _validate(header_lang)

    query_lang = request.query_params.get("language")
    if query_lang:
        return _validate(query_lang)

    # Body fallback (JSON or form/multipart)
    content_type = request.headers.get("content-type", "")

    # Cache parsed body so multiple calls won't re-consume the stream.
    if hasattr(request.state, "_dashen_language_body"):
        body_lang = getattr(request.state, "_dashen_language_body")
        if isinstance(body_lang, str) and body_lang:
            return _validate(body_lang)
        return "en"

    body_lang: Optional[str] = None

    try:
        if "application/json" in content_type:
            data = await request.json()
            if isinstance(data, dict) and isinstance(data.get("language"), str):
                body_lang = data.get("language")
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            lang_val = form.get("language")
            if isinstance(lang_val, str):
                body_lang = lang_val
    except Exception:
        body_lang = None

    request.state._dashen_language_body = body_lang

    if body_lang:
        return _validate(body_lang)

    return "en"
