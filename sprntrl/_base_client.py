from __future__ import annotations

import os
import time
import asyncio
import random
from typing import Any, Mapping, Union
from urllib.parse import urljoin

import httpx

from ._errors import (
    APIConnectionError,
    APIConnectionTimeoutError,
    error_for_status,
    SprntrlError,
)


DEFAULT_BASE_URL = "https://api.supernatural.sh"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
_USER_AGENT = "sprntrl-python/0.1.0"

JSONLike = Union[Mapping[str, Any], list, str, int, float, bool, None]


class _BaseClient:
    """Shared config and helpers for sync and async clients."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        api_key = api_key or os.environ.get("SPRNTRL_API_KEY")
        if not api_key:
            raise SprntrlError(
                "No API key provided. Pass api_key= or set SPRNTRL_API_KEY."
            )
        base_url = base_url or os.environ.get("SPRNTRL_BASE_URL") or DEFAULT_BASE_URL
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = dict(default_headers or {})

    def _headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        h = {
            "Authorization": f"ApiKey {self.api_key}",
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
            **self._default_headers,
        }
        if extra:
            h.update(extra)
        return h

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    @staticmethod
    def _should_retry(exc: Exception | None, status: int | None) -> bool:
        if exc is not None:
            return True  # connection-level errors
        if status is None:
            return False
        return status == 408 or status == 409 or status == 429 or status >= 500

    @staticmethod
    def _backoff(attempt: int) -> float:
        # 0.5s, 1s, 2s + jitter
        base = 0.5 * (2 ** attempt)
        return base + random.uniform(0, 0.25)

    @staticmethod
    def _parse_error(response: httpx.Response) -> tuple[str, Any]:
        body: Any = None
        try:
            body = response.json()
        except Exception:
            body = response.text
        msg = None
        if isinstance(body, dict):
            msg = body.get("error") or body.get("message") or body.get("detail")
        if not msg:
            msg = f"HTTP {response.status_code}"
        return msg, body


class SyncClient(_BaseClient):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._http = httpx.Client(timeout=self.timeout)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SyncClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: JSONLike = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Any = None,
        data: Any = None,
        stream: bool = False,
    ) -> Any:
        url = self._url(path)
        h = self._headers(headers)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.request(
                    method,
                    url,
                    json=json if files is None and data is None else None,
                    params=params,
                    headers=h,
                    files=files,
                    data=data,
                )
            except httpx.TimeoutException as exc:
                last_exc = APIConnectionTimeoutError(str(exc))
            except httpx.RequestError as exc:
                last_exc = APIConnectionError(str(exc), cause=exc)
            else:
                status = response.status_code
                if 200 <= status < 300:
                    if stream:
                        return response
                    if not response.content:
                        return None
                    ctype = response.headers.get("content-type", "")
                    if "application/json" in ctype:
                        return response.json()
                    return response.content
                if self._should_retry(None, status) and attempt < self.max_retries:
                    time.sleep(self._backoff(attempt))
                    continue
                msg, body = self._parse_error(response)
                raise error_for_status(status, msg, body=body)
            if attempt < self.max_retries:
                time.sleep(self._backoff(attempt))
                continue
            raise last_exc
        assert last_exc is not None
        raise last_exc


class AsyncClient(_BaseClient):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._http = httpx.AsyncClient(timeout=self.timeout)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: JSONLike = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Any = None,
        data: Any = None,
        stream: bool = False,
    ) -> Any:
        url = self._url(path)
        h = self._headers(headers)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.request(
                    method,
                    url,
                    json=json if files is None and data is None else None,
                    params=params,
                    headers=h,
                    files=files,
                    data=data,
                )
            except httpx.TimeoutException as exc:
                last_exc = APIConnectionTimeoutError(str(exc))
            except httpx.RequestError as exc:
                last_exc = APIConnectionError(str(exc), cause=exc)
            else:
                status = response.status_code
                if 200 <= status < 300:
                    if stream:
                        return response
                    if not response.content:
                        return None
                    ctype = response.headers.get("content-type", "")
                    if "application/json" in ctype:
                        return response.json()
                    return response.content
                if self._should_retry(None, status) and attempt < self.max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                msg, body = self._parse_error(response)
                raise error_for_status(status, msg, body=body)
            if attempt < self.max_retries:
                await asyncio.sleep(self._backoff(attempt))
                continue
            raise last_exc
        assert last_exc is not None
        raise last_exc
