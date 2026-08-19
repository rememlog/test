import json
from typing import Any

from redis import Redis

from app.core.config import settings


class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)

    def set_json(self, key: str, payload: Any, ttl: int = 300) -> None:
        self.redis.setex(key, ttl, json.dumps(payload, ensure_ascii=False, default=str))

    def get_json(self, key: str) -> Any | None:
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def ping(self) -> bool:
        return bool(self.redis.ping())
