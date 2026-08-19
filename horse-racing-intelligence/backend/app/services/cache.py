import json
from redis import Redis
from app.core.config import settings


class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def set_json(self, key: str, payload: dict, ttl: int = 60) -> None:
        self.redis.setex(key, ttl, json.dumps(payload, ensure_ascii=False))

    def get_json(self, key: str):
        value = self.redis.get(key)
        return json.loads(value) if value else None
