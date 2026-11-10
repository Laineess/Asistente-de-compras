from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def build_llm() -> BaseChatModel | None:
    if not settings.gemini_api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.2,
        max_output_tokens=2048,
        model_kwargs={"transport": "rest"},
    )


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def invoke_text(llm: BaseChatModel | None, prompt: str) -> str | None:
    if llm is None:
        return None
    try:
        response = llm.invoke(prompt)
    except Exception:
        return None
    text = content_to_text(getattr(response, "content", "")).strip()
    return text or None


def parse_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def invoke_json(llm: BaseChatModel | None, prompt: str) -> dict[str, Any] | None:
    text = invoke_text(llm, prompt)
    if not text:
        return None
    return parse_json(text)
