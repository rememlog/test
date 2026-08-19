import httpx
from app.core.config import settings


class KRAClient:
    """Adapter boundary for Korea Racing Authority open APIs."""

    def __init__(self):
        self.base_url = settings.kra_api_base_url.rstrip("/")
        self.service_key = settings.kra_service_key

    @property
    def configured(self) -> bool:
        return bool(self.service_key)

    async def get_json(self, path: str, params: dict | None = None) -> dict:
        if not self.configured:
            raise RuntimeError("KRA_SERVICE_KEY is not configured")
        query = dict(params or {})
        query["serviceKey"] = self.service_key
        query.setdefault("_type", "json")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/{path.lstrip('/')}" , params=query)
            response.raise_for_status()
            return response.json()
