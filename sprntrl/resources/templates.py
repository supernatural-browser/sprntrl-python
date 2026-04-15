from __future__ import annotations

from typing import TYPE_CHECKING

from .._types import Template

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


class Templates:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def list(self) -> list[Template]:
        resp = self._client._request("GET", "/api/v1/templates")
        return resp.get("templates", [])


class AsyncTemplates:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(self) -> list[Template]:
        resp = await self._client._request("GET", "/api/v1/templates")
        return resp.get("templates", [])
