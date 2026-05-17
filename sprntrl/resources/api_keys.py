from __future__ import annotations

from typing import TYPE_CHECKING

from .._types import APIKey, APIKeyCreated
from .._utils import seg

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


class APIKeys:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def list(self) -> list[APIKey]:
        resp = self._client._request("GET", "/api/v1/apikeys")
        return resp.get("api_keys", [])

    def create(self, name: str) -> APIKeyCreated:
        """Create an API key. The full `key` field is returned ONLY on creation;
        store it immediately — the server cannot show it again."""
        return self._client._request("POST", "/api/v1/apikeys", json={"name": name})

    def revoke(self, key_id: str) -> None:
        self._client._request("DELETE", f"/api/v1/apikeys/{seg(key_id)}")


class AsyncAPIKeys:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(self) -> list[APIKey]:
        resp = await self._client._request("GET", "/api/v1/apikeys")
        return resp.get("api_keys", [])

    async def create(self, name: str) -> APIKeyCreated:
        return await self._client._request(
            "POST", "/api/v1/apikeys", json={"name": name}
        )

    async def revoke(self, key_id: str) -> None:
        await self._client._request("DELETE", f"/api/v1/apikeys/{seg(key_id)}")
