from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.config.config import config


client = QdrantClient(url=config.QDRANT_URL, timeout=60)


def ensure_collection(collection_name: str, *, dim: int = config.EMBEDDING_DIM) -> None:
    """
    创建或确保 Qdrant collection 存在。
    """
    try:
        col = client.get_collection(collection_name=collection_name)
        # 如果 collection 已存在但向量维度不同，需要重建。
        existing_dim = (
            col.config.params.vectors.size
            if getattr(col, "config", None)
            and getattr(col.config, "params", None)
            and getattr(col.config.params, "vectors", None)
            else None
        )
        if existing_dim is not None and int(existing_dim) != int(dim):
            client.delete_collection(collection_name=collection_name)
        else:
            return
    except Exception:
        # collection 不存在或连接失败
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Qdrant payload 需要 JSON 可序列化的类型；复杂对象转为字符串。
    """
    sanitized: dict[str, Any] = {}
    for k, v in payload.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            sanitized[k] = v
        else:
            sanitized[k] = str(v)
    return sanitized


def upsert_chunks(
    *,
    collection_name: str,
    vectors: list[list[float]],
    ids: list[str],
    payloads: list[dict[str, Any]],
) -> None:
    if not (len(vectors) == len(ids) == len(payloads)):
        raise ValueError("vectors / ids / payloads must have the same length")

    points = [
        PointStruct(id=point_id, vector=vec, payload=_sanitize_payload(payload))
        for point_id, vec, payload in zip(ids, vectors, payloads)
    ]
    if not points:
        return

    client.upsert(collection_name=collection_name, points=points)


def search(
    *,
    collection_name: str,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    # 使用HTTP客户端直接调用Qdrant API
    import requests
    import json
    
    url = f"{config.QDRANT_URL}/collections/{collection_name}/points/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "vector": query_vector,
        "limit": top_k,
        "with_payload": True
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    
    res = response.json()
    results: list[dict[str, Any]] = []
    
    for hit in res.get("result", []):
        results.append(
            {
                "id": hit.get("id"),
                "score": float(hit.get("score", 0.0)),
                "payload": hit.get("payload", {})
            }
        )
    return results

