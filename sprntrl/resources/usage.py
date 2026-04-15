from __future__ import annotations

from typing import TYPE_CHECKING

from .._types import Usage as UsageModel, UsageMonth

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


class Usage:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def current(self) -> UsageModel:
        return self._client._request("GET", "/api/v1/usage")

    def history(self) -> list[UsageMonth]:
        resp = self._client._request("GET", "/api/v1/usage/history")
        return resp.get("months", [])


class AsyncUsage:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def current(self) -> UsageModel:
        return await self._client._request("GET", "/api/v1/usage")

    async def history(self) -> list[UsageMonth]:
        resp = await self._client._request("GET", "/api/v1/usage/history")
        return resp.get("months", [])
