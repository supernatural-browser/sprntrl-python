from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._types import IPWhitelistEntry
from .._utils import seg

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


def _body(ip: str, label: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {"ip": ip}
    if label is not None:
        body["label"] = label
    return body


class IPWhitelist:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def list(self) -> list[IPWhitelistEntry]:
        resp = self._client._request("GET", "/api/v1/settings/ip-whitelist")
        return resp.get("entries", [])

    def add(self, ip: str = "current", *, label: str | None = None) -> IPWhitelistEntry:
        """Add an IP to the whitelist. Pass ip='current' to register the caller's
        public IP as seen by the API (via CF-Connecting-IP)."""
        return self._client._request(
            "POST", "/api/v1/settings/ip-whitelist", json=_body(ip, label)
        )

    def remove(self, entry_id: str) -> None:
        self._client._request(
            "DELETE", f"/api/v1/settings/ip-whitelist/{seg(entry_id)}"
        )


class AsyncIPWhitelist:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(self) -> list[IPWhitelistEntry]:
        resp = await self._client._request("GET", "/api/v1/settings/ip-whitelist")
        return resp.get("entries", [])

    async def add(self, ip: str = "current", *, label: str | None = None) -> IPWhitelistEntry:
        return await self._client._request(
            "POST", "/api/v1/settings/ip-whitelist", json=_body(ip, label)
        )

    async def remove(self, entry_id: str) -> None:
        await self._client._request(
            "DELETE", f"/api/v1/settings/ip-whitelist/{seg(entry_id)}"
        )
