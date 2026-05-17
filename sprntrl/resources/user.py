from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._types import ChangePasswordResult, User as UserModel

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


class User:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def me(self) -> UserModel:
        return self._client._request("GET", "/api/v1/user/me")

    def update(self, *, name: str | None = None) -> UserModel:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        return self._client._request("PUT", "/api/v1/user/me", json=body)

    def get_settings(self) -> UserModel:
        """Read the account settings (same shape as ``me()``)."""
        return self._client._request("GET", "/api/v1/user/me/settings")

    def update_settings(self, **fields: Any) -> UserModel:
        return self._client._request("PUT", "/api/v1/user/me/settings", json=fields)

    def change_password(
        self, current_password: str, new_password: str
    ) -> ChangePasswordResult:
        return self._client._request(
            "PUT",
            "/api/v1/user/change-password",
            json={"current_password": current_password, "new_password": new_password},
        )


class AsyncUser:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def me(self) -> UserModel:
        return await self._client._request("GET", "/api/v1/user/me")

    async def update(self, *, name: str | None = None) -> UserModel:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        return await self._client._request("PUT", "/api/v1/user/me", json=body)

    async def get_settings(self) -> UserModel:
        """Read the account settings (same shape as ``me()``)."""
        return await self._client._request("GET", "/api/v1/user/me/settings")

    async def update_settings(self, **fields: Any) -> UserModel:
        return await self._client._request(
            "PUT", "/api/v1/user/me/settings", json=fields
        )

    async def change_password(
        self, current_password: str, new_password: str
    ) -> ChangePasswordResult:
        return await self._client._request(
            "PUT",
            "/api/v1/user/change-password",
            json={"current_password": current_password, "new_password": new_password},
        )
