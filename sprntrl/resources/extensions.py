from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Union

from .._errors import SprntrlError
from .._types import SessionExtension
from .._utils import seg

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


ExtensionUpload = Union[bytes, BinaryIO]


def _validate_add_args(
    *,
    upload: ExtensionUpload | None,
    webstore_url: str | None,
    crx_url: str | None,
) -> None:
    """Exactly one source must be set. Raise with a friendly message
    rather than letting the API return a less-clear 400."""
    sources = sum(1 for v in (upload, webstore_url, crx_url) if v is not None)
    if sources != 1:
        raise SprntrlError(
            "extensions.add: provide exactly one of upload, webstore_url, crx_url"
        )


class SessionExtensions:
    """Manage Chrome extensions attached to a persistent session's profile.

    Extensions are loaded at Chrome launch via ``--load-extension`` so
    install/remove/toggle take effect on the **next** session start. Stop
    and resume the session to apply changes immediately.

    For ephemeral sessions, pass an ``extensions`` list to
    :py:meth:`Sessions.create` instead — these endpoints only apply to
    persistent sessions.
    """

    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def list(self, session_id: str) -> list[SessionExtension]:
        resp = self._client._request(
            "GET", f"/api/v1/sessions/{seg(session_id)}/extensions"
        )
        return resp.get("extensions", []) if isinstance(resp, dict) else []

    def add(
        self,
        session_id: str,
        *,
        upload: ExtensionUpload | None = None,
        filename: str | None = None,
        webstore_url: str | None = None,
        crx_url: str | None = None,
    ) -> SessionExtension:
        """Install or replace an extension. One source must be set:
        ``upload`` (bytes or file-like; up to 50 MiB) plus optional
        ``filename``; ``webstore_url`` (Chrome Web Store detail URL or
        bare 32-char extension ID); or ``crx_url`` (direct HTTPS URL).
        """
        _validate_add_args(upload=upload, webstore_url=webstore_url, crx_url=crx_url)
        path = f"/api/v1/sessions/{seg(session_id)}/extensions"
        if upload is not None:
            files = {
                "file": (
                    filename or "extension.zip",
                    upload,
                    "application/octet-stream",
                )
            }
            return self._client._request("POST", path, files=files)
        body: dict[str, str] = {}
        if webstore_url is not None:
            body["source"] = "webstore"
            body["url"] = webstore_url
        else:
            body["source"] = "crx_url"
            body["url"] = crx_url  # type: ignore[assignment]
        return self._client._request("POST", path, json=body)

    def set_enabled(self, session_id: str, extension_id: str, enabled: bool) -> None:
        self._client._request(
            "PATCH",
            f"/api/v1/sessions/{seg(session_id)}/extensions/{seg(extension_id)}",
            json={"enabled": enabled},
        )

    def remove(self, session_id: str, extension_id: str) -> None:
        self._client._request(
            "DELETE",
            f"/api/v1/sessions/{seg(session_id)}/extensions/{seg(extension_id)}",
        )


class AsyncSessionExtensions:
    """Async variant of :py:class:`SessionExtensions`. Same wire format,
    same constraints."""

    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(self, session_id: str) -> list[SessionExtension]:
        resp = await self._client._request(
            "GET", f"/api/v1/sessions/{seg(session_id)}/extensions"
        )
        return resp.get("extensions", []) if isinstance(resp, dict) else []

    async def add(
        self,
        session_id: str,
        *,
        upload: ExtensionUpload | None = None,
        filename: str | None = None,
        webstore_url: str | None = None,
        crx_url: str | None = None,
    ) -> SessionExtension:
        _validate_add_args(upload=upload, webstore_url=webstore_url, crx_url=crx_url)
        path = f"/api/v1/sessions/{seg(session_id)}/extensions"
        if upload is not None:
            files = {
                "file": (
                    filename or "extension.zip",
                    upload,
                    "application/octet-stream",
                )
            }
            return await self._client._request("POST", path, files=files)
        body: dict[str, str] = {}
        if webstore_url is not None:
            body["source"] = "webstore"
            body["url"] = webstore_url
        else:
            body["source"] = "crx_url"
            body["url"] = crx_url  # type: ignore[assignment]
        return await self._client._request("POST", path, json=body)

    async def set_enabled(self, session_id: str, extension_id: str, enabled: bool) -> None:
        await self._client._request(
            "PATCH",
            f"/api/v1/sessions/{seg(session_id)}/extensions/{seg(extension_id)}",
            json={"enabled": enabled},
        )

    async def remove(self, session_id: str, extension_id: str) -> None:
        await self._client._request(
            "DELETE",
            f"/api/v1/sessions/{seg(session_id)}/extensions/{seg(extension_id)}",
        )
