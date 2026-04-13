from __future__ import annotations

from http import HTTPStatus
from typing import Iterable

import dashscope

from app.config.config import config


if config.DASH_SCOPE_API_KEY:
    # dashscope SDK 内部会读取该字段，用于鉴权。
    dashscope.api_key = config.DASH_SCOPE_API_KEY


def embed_text(text: str) -> list[float]:
    """
    调用 DashScope 的 TextEmbedding 获取向量。
    """
    if not config.DASH_SCOPE_API_KEY:
        raise RuntimeError("Missing dashscope api key: set DASHSCOPE_API_KEY (or API_KEY).")

    if not text:
        raise ValueError("text is empty")

    resp = dashscope.TextEmbedding.call(model=config.EMBEDDING_MODEL, input=text)
    if resp.status_code != HTTPStatus.OK:
        # resp.message / resp.code 字段用于定位错误
        raise RuntimeError(f"Embedding call failed: status={resp.status_code}, code={getattr(resp, 'code', '')}, message={getattr(resp, 'message', '')}")

    # resp.output["embeddings"][0]["embedding"] 结构（SDK 的常见返回结构）
    output = getattr(resp, "output", None) or {}
    embeddings = output.get("embeddings") if isinstance(output, dict) else None
    if not embeddings:
        raise RuntimeError(f"Unexpected embedding response format: {resp}")

    embedding = embeddings[0].get("embedding")
    if not embedding:
        raise RuntimeError(f"Unexpected embedding response format: {resp}")

    return list(embedding)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """
    MVP：按顺序逐条 embedding（简单可靠，便于排查）。
    """
    return [embed_text(t) for t in texts]

