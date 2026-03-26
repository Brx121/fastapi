from __future__ import annotations


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """
    最小可用的文本分块：按字符长度切分，并使用 overlap 保留边界信息。
    MVP 场景下不依赖分词器/模型 token 预算。
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # 简单清理：多余空白会影响“上下文拼接”的可读性
    normalized = "\n".join([line.strip() for line in normalized.split("\n") if line.strip()])
    if not normalized:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start += step
    return chunks

