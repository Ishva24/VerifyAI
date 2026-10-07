import httpx
from typing import Any

from app.config import settings


async def call_ai_service(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.ai_service_url}/detect", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
