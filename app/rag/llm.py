from __future__ import annotations

from http import HTTPStatus

import dashscope

from app.config.config import config


if config.DASH_SCOPE_API_KEY:
    dashscope.api_key = config.DASH_SCOPE_API_KEY


def generate_chat(messages: list[dict], *, model: str | None = None) -> str:
    """
    使用 DashScope Generation 生成回复。
    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    """
    if not config.DASH_SCOPE_API_KEY:
        raise RuntimeError("Missing dashscope api key: set DASHSCOPE_API_KEY (or API_KEY).")

    resp = dashscope.Generation.call(
        api_key=config.DASH_SCOPE_API_KEY,
        model=model or config.MODEL,
        messages=messages,
        result_format="message",
    )

    if resp.status_code != HTTPStatus.OK:
        raise RuntimeError(
            f"Generation call failed: status={resp.status_code}, code={getattr(resp, 'code', '')}, message={getattr(resp, 'message', '')}"
        )

    output = getattr(resp, "output", None) or {}
    choices = None
    if isinstance(output, dict):
        choices = output.get("choices")

    # 常见结构：output.choices[0].message.content
    if choices and isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            msg = first.get("message") or {}
            content = msg.get("content")
            if content:
                return str(content)

    # 兜底：有些模型返回 output.text
    if isinstance(output, dict) and output.get("text"):
        return str(output["text"])

    raise RuntimeError(f"Unexpected Generation response format: {resp}")

