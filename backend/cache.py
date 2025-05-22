import redis
import os
import json
from typing import Optional, Any

# Redis接続設定
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(redis_url)

def get_cache(key: str) -> Optional[Any]:
    """キャッシュからデータを取得"""
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_cache(key: str, value: Any, expire: int = 3600) -> None:
    """データをキャッシュに保存（デフォルト1時間）"""
    redis_client.setex(key, expire, json.dumps(value))

def delete_cache(key: str) -> None:
    """キャッシュを削除"""
    redis_client.delete(key) 