from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._types import Profile
from .._utils import seg

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


def _build_create_body(
    name: str,
    *,
    template_id: str | None = None,
    config: Any = None,
    description: str | None = None,
    os: str | None = None,
    location: str | None = None,
    persona: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name}
    if template_id is not None:
        body["template_id"] = template_id
    if config is not None:
        body["config_json"] = config
    if description is not None:
        body["description"] = description
    if os is not None:
        body["os"] = os
    if location is not None:
        body["location"] = location
    if persona is not None:
        body["persona"] = persona
    return body


class Profiles:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def create(self, name: str, **kwargs: Any) -> Profile:
        return self._client._request(
            "POST", "/api/v1/profiles", json=_build_create_body(name, **kwargs)
        )

    def list(self) -> list[Profile]:
        resp = self._client._request("GET", "/api/v1/profiles")
        return resp.get("profiles", [])

    def get(self, profile_id: str) -> Profile:
        return self._client._request("GET", f"/api/v1/profiles/{seg(profile_id)}")

    def update(self, profile_id: str, **fields: Any) -> Profile:
        return self._client._request(
            "PUT", f"/api/v1/profiles/{seg(profile_id)}", json=fields
        )

    def duplicate(self, profile_id: str) -> Profile:
        return self._client._request(
            "POST", f"/api/v1/profiles/{seg(profile_id)}/duplicate"
        )

    def delete(self, profile_id: str) -> None:
        self._client._request("DELETE", f"/api/v1/profiles/{seg(profile_id)}")


class AsyncProfiles:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def create(self, name: str, **kwargs: Any) -> Profile:
        return await self._client._request(
            "POST", "/api/v1/profiles", json=_build_create_body(name, **kwargs)
        )

    async def list(self) -> list[Profile]:
        resp = await self._client._request("GET", "/api/v1/profiles")
        return resp.get("profiles", [])

    async def get(self, profile_id: str) -> Profile:
        return await self._client._request("GET", f"/api/v1/profiles/{seg(profile_id)}")

    async def update(self, profile_id: str, **fields: Any) -> Profile:
        return await self._client._request(
            "PUT", f"/api/v1/profiles/{seg(profile_id)}", json=fields
        )

    async def duplicate(self, profile_id: str) -> Profile:
        return await self._client._request(
            "POST", f"/api/v1/profiles/{seg(profile_id)}/duplicate"
        )

    async def delete(self, profile_id: str) -> None:
        await self._client._request("DELETE", f"/api/v1/profiles/{seg(profile_id)}")
