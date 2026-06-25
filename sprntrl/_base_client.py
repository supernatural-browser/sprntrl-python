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
from ._version import __version__


DEFAULT_BASE_URL = "https://api.supernatural.sh"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
_USER_AGENT = f"sprntrl-python/{__version__}"

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

    # Codes the server sends on a 429 that represents a non-transient
    # quota/capacity limit (at your concurrent-session cap, out of plan usage,
    # etc.). Waiting does NOT clear these — only changing state (stopping a
    # session, upgrading) does — so retrying just amplifies load and can never
    # succeed. A 429 without one of these codes (or with "rate_limited") is a
    # real throttle and stays retryable.
    _NON_RETRYABLE_429_CODES = frozenset({
        "concurrent_session_limit",
        "usage_limit_exceeded",
        "persistent_profile_limit",
        "bandwidth_limit_reached",
        "byo_not_supported",
    })

    @classmethod
    def _should_retry(cls, exc: Exception | None, status: int | None, code: str | None = None) -> bool:
        if exc is not None:
            return True  # connection-level errors
        if status is None:
            return False
        if status == 429:
            return code not in cls._NON_RETRYABLE_429_CODES
        # 408 Request Timeout and 5xx are transient. 409 Conflict is a state
        # conflict (e.g. profile already exists) — retrying won't help.
        return status == 408 or status >= 500

    @staticmethod
    def _backoff(attempt: int) -> float:
        # 0.5s, 1s, 2s + jitter
        base = 0.5 * (2 ** attempt)
        return base + random.uniform(0, 0.25)

    @staticmethod
    def _error_code(response: httpx.Response) -> str | None:
        """The machine-readable `code` from a JSON error body, if any."""
        try:
            body = response.json()
        except Exception:
            return None
        if isinstance(body, dict) and isinstance(body.get("code"), str):
            return body["code"]
        return None

    @classmethod
    def _retry_delay(cls, attempt: int, response: httpx.Response) -> float:
        """Honor a server Retry-After (seconds) when present — capped so a
        large value can't hang the caller — else exponential backoff."""
        ra = response.headers.get("Retry-After")
        if ra:
            try:
                return max(0.0, min(float(ra), 30.0))
            except ValueError:
                pass
        return cls._backoff(attempt)

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
                code = self._error_code(response)
                if self._should_retry(None, status, code) and attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt, response))
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
                code = self._error_code(response)
                if self._should_retry(None, status, code) and attempt < self.max_retries:
                    await asyncio.sleep(self._retry_delay(attempt, response))
                    continue
                msg, body = self._parse_error(response)
                raise error_for_status(status, msg, body=body)
            if attempt < self.max_retries:
                await asyncio.sleep(self._backoff(attempt))
                continue
            raise last_exc
        assert last_exc is not None
        raise last_exc
