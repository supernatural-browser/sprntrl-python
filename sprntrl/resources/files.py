from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO, Union

from .._types import FileInfo

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


FileContent = Union[bytes, BinaryIO]


def _parse_list(resp: Any) -> list[FileInfo]:
    if isinstance(resp, dict):
        return resp.get("files", [])
    if isinstance(resp, list):
        return resp
    return []


class SessionFiles:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client

    def list(self, session_id: str) -> list[FileInfo]:
        resp = self._client._request(
            "GET", f"/api/v1/sessions/{session_id}/files"
        )
        return _parse_list(resp)

    def download(self, session_id: str, filename: str) -> bytes:
        resp = self._client._request(
            "GET", f"/api/v1/sessions/{session_id}/files/{filename}"
        )
        if isinstance(resp, (bytes, bytearray)):
            return bytes(resp)
        if resp is None:
            return b""
        # JSON-ish error falls through; normally we get bytes
        return resp

    def upload(
        self,
        session_id: str,
        filename: str,
        content: FileContent,
        *,
        content_type: str = "application/octet-stream",
    ) -> None:
        files = {"file": (filename, content, content_type)}
        self._client._request(
            "POST", f"/api/v1/sessions/{session_id}/files", files=files
        )


class AsyncSessionFiles:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(self, session_id: str) -> list[FileInfo]:
        resp = await self._client._request(
            "GET", f"/api/v1/sessions/{session_id}/files"
        )
        return _parse_list(resp)

    async def download(self, session_id: str, filename: str) -> bytes:
        resp = await self._client._request(
            "GET", f"/api/v1/sessions/{session_id}/files/{filename}"
        )
        if isinstance(resp, (bytes, bytearray)):
            return bytes(resp)
        if resp is None:
            return b""
        return resp

    async def upload(
        self,
        session_id: str,
        filename: str,
        content: FileContent,
        *,
        content_type: str = "application/octet-stream",
    ) -> None:
        files = {"file": (filename, content, content_type)}
        await self._client._request(
            "POST", f"/api/v1/sessions/{session_id}/files", files=files
        )
