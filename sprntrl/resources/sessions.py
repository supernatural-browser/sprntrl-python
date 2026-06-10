from __future__ import annotations

import time
import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, Mapping
from urllib.parse import urlparse, urlunparse

from .._types import OS, ProxyConfig, Session, PaginatedSessions, ExtensionInlineSpec
from .._errors import SprntrlError
from .._utils import seg

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


def _normalize_proxy(proxy: str | Mapping[str, Any] | None) -> dict[str, Any]:
    """Convert a proxy URL string or dict into the flat fields the API expects."""
    if proxy is None:
        return {}
    if isinstance(proxy, str):
        parsed = urlparse(proxy)
        if not parsed.scheme or not parsed.hostname:
            raise SprntrlError(f"Invalid proxy URL: {proxy!r}")
        out = {
            "proxy_protocol": parsed.scheme.upper(),
            "proxy_host": parsed.hostname,
        }
        if parsed.port is not None:
            out["proxy_port"] = parsed.port
        if parsed.username:
            out["proxy_username"] = parsed.username
        if parsed.password:
            out["proxy_password"] = parsed.password
        return out
    out = {}
    if "protocol" in proxy:
        out["proxy_protocol"] = str(proxy["protocol"]).upper()
    for src, dst in (
        ("host", "proxy_host"),
        ("port", "proxy_port"),
        ("username", "proxy_username"),
        ("password", "proxy_password"),
    ):
        if src in proxy and proxy[src] is not None:
            out[dst] = proxy[src]
    return out


def _normalize_extensions(extensions: list[ExtensionInlineSpec] | None) -> list[dict[str, Any]]:
    """Convert SDK ExtensionInlineSpec dicts to the wire shape the API expects.

    Each entry must set exactly one source. Extras are silently dropped so
    a caller passing a typo doesn't paper over the missing source.
    """
    if not extensions:
        return []
    out: list[dict[str, Any]] = []
    for i, spec in enumerate(extensions):
        sources = sum(
            1 for k in ("upload_b64", "webstore_url", "crx_url")
            if spec.get(k)  # type: ignore[arg-type]
        )
        if sources != 1:
            raise SprntrlError(
                f"extensions[{i}]: provide exactly one of upload_b64, webstore_url, crx_url"
            )
        entry: dict[str, Any] = {}
        for key in ("upload_b64", "filename", "webstore_url", "crx_url"):
            if spec.get(key):  # type: ignore[arg-type]
                entry[key] = spec[key]  # type: ignore[index]
        out.append(entry)
    return out


def _build_create_body(
    os: OS,
    location: str,
    *,
    persistent: bool = False,
    captcha_solver: bool = False,
    isolated_world: bool | None = None,
    headless: bool | None = None,
    block_images: bool = False,
    session_name: str | None = None,
    proxy: str | Mapping[str, Any] | None = None,
    extensions: list[ExtensionInlineSpec] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "os": os,
        "location": location,
        "persistent": persistent,
    }
    if captcha_solver:
        body["captcha_solver"] = True
    if isolated_world is not None:
        body["isolated_world"] = isolated_world
    if headless is not None:
        body["headless"] = headless
    if block_images:
        body["block_images"] = True
    if session_name is not None:
        body["session_name"] = session_name
    body.update(_normalize_proxy(proxy))
    ext_payload = _normalize_extensions(extensions)
    if ext_payload:
        body["extensions"] = ext_payload
    return body


class Sessions:
    def __init__(self, client: "SyncClient") -> None:
        self._client = client
        from .files import SessionFiles
        from .extensions import SessionExtensions
        self.files = SessionFiles(client)
        self.extensions = SessionExtensions(client)

    def create(
        self,
        os: OS,
        location: str,
        *,
        persistent: bool = False,
        captcha_solver: bool = False,
        isolated_world: bool | None = None,
        headless: bool | None = None,
        block_images: bool = False,
        session_name: str | None = None,
        proxy: str | ProxyConfig | None = None,
        extensions: list[ExtensionInlineSpec] | None = None,
    ) -> Session:
        """Create a stealth browser session.

        ``isolated_world`` controls whether automation runs in a V8 world
        hidden from the page (default: True on the server). Leave as ``None``
        to use the platform default. Pass ``False`` only when you must read
        page-defined JavaScript globals or call ``window.*`` page functions —
        main-world execution is visible to anti-bot detection.

        ``headless`` launches Chrome with ``--headless=new``. Default ``True``
        on the server for SDK callers — pass ``False`` if you also want a
        live VNC viewer of the session (e.g. for human-assisted debugging).
        Leave as ``None`` to use the platform default.

        ``block_images`` launches Chrome with
        ``--blink-settings=imagesEnabled=false`` (default False) — speeds
        up loads and cuts bandwidth on image-heavy sites.

        ``extensions`` ships Chrome extensions for the session to load at
        Chrome launch. Only honoured for ephemeral sessions — persistent
        sessions manage extensions via ``client.sessions.extensions.*`` so
        the set survives stop/resume cycles. Each spec sets exactly one of
        ``upload_b64`` (base64 ZIP/CRX bytes), ``webstore_url`` (Chrome
        Web Store URL or ID), or ``crx_url`` (direct HTTPS URL to a .crx).
        """
        body = _build_create_body(
            os, location,
            persistent=persistent,
            captcha_solver=captcha_solver,
            isolated_world=isolated_world,
            headless=headless,
            block_images=block_images,
            session_name=session_name,
            proxy=proxy,
            extensions=extensions,
        )
        return self._client._request("POST", "/api/v1/sessions", json=body)

    def list(self) -> list[Session]:
        resp = self._client._request("GET", "/api/v1/sessions")
        return resp.get("sessions", [])

    def list_active(self) -> list[Session]:
        resp = self._client._request("GET", "/api/v1/sessions/active")
        return resp.get("sessions", [])

    def list_history(self, *, page: int = 1, per_page: int = 25) -> PaginatedSessions:
        return self._client._request(
            "GET",
            "/api/v1/sessions/history",
            params={"page": page, "per_page": per_page},
        )

    def list_resumable(self, *, limit: int = 10) -> list[Session]:
        resp = self._client._request(
            "GET", "/api/v1/sessions/resumable", params={"limit": limit}
        )
        return resp.get("sessions", [])

    def list_persistent(self) -> list[Session]:
        """Persistent sessions (created with persistent=True), whether
        currently running or stopped-but-resumable."""
        resp = self._client._request("GET", "/api/v1/sessions/persistent")
        return resp.get("sessions", [])

    def list_locations(self) -> list[str]:
        resp = self._client._request("GET", "/api/v1/sessions/locations")
        return resp.get("locations", [])

    def get(self, session_id: str) -> Session:
        return self._client._request("GET", f"/api/v1/sessions/{seg(session_id)}")

    def stop(self, session_id: str) -> None:
        self._client._request("DELETE", f"/api/v1/sessions/{seg(session_id)}")

    def resume(
        self,
        session_id: str,
        *,
        proxy: str | ProxyConfig | None = None,
    ) -> Session:
        """Resume a stopped persistent session.

        By default the proxy used at the previous run is reused. Pass
        ``proxy`` (URL string or ``ProxyConfig``) to switch to a different
        BYO proxy for this and future resumes. OS, location, and the
        fingerprint pin are immutable after create.
        """
        body = _normalize_proxy(proxy)
        return self._client._request(
            "POST",
            f"/api/v1/sessions/{seg(session_id)}/resume",
            json=body if body else None,
        )

    def delete_persistent(self, session_id: str) -> None:
        self._client._request(
            "DELETE", f"/api/v1/sessions/{seg(session_id)}/persist"
        )

    def wait_until_ready(
        self,
        session_id: str,
        *,
        timeout: float = 60.0,
        poll_interval: float = 0.5,
    ) -> Session:
        deadline = time.monotonic() + timeout
        while True:
            session = self.get(session_id)
            status = session.get("status")
            if status == "running":
                return session
            if status in ("failed", "stopped", "stopping"):
                raise SprntrlError(
                    f"Session {session_id} entered status {status!r} while waiting"
                )
            if time.monotonic() >= deadline:
                raise SprntrlError(
                    f"Session {session_id} not ready after {timeout}s (status={status!r})"
                )
            time.sleep(poll_interval)

    def connect(
        self,
        session_id: str,
        *,
        framework: str = "playwright",
        auto_whitelist: bool = False,
        wait: bool = True,
        wait_timeout: float = 60.0,
    ) -> Any:
        """Connect Playwright or Puppeteer to a session's CDP endpoint.

        The CDP endpoint is IP-whitelist gated (no bearer auth on the socket), so
        the caller's IP must already be in the account's whitelist. Pass
        auto_whitelist=True to register the current IP first.
        """
        from ..lib.browser import connect_sync
        if wait:
            session = self.wait_until_ready(session_id, timeout=wait_timeout)
        else:
            session = self.get(session_id)
        return connect_sync(
            self._client, session, framework=framework, auto_whitelist=auto_whitelist
        )

    def cdp_url(self, session_id: str) -> str:
        """Return the CDP WebSocket URL for a session. Callers can hand this to
        any CDP client (chrome-remote-interface-python, raw websockets, etc.)."""
        parsed = urlparse(self._client.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((
            scheme, parsed.netloc, f"/api/v1/sessions/{seg(session_id)}/cdp", "", "", "",
        ))

    @contextlib.contextmanager
    def browser_session(
        self,
        session_id: str,
        *,
        framework: str = "playwright",
        auto_whitelist: bool = False,
        wait: bool = True,
        wait_timeout: float = 60.0,
    ) -> Iterator[Any]:
        """Context manager that connects a browser and tears everything down on exit.

        Yields a connected Playwright Browser. On exit, closes the browser and
        stops the Playwright driver. Does NOT stop the session — the caller
        owns the session's lifecycle.

            with client.sessions.browser_session(sid, auto_whitelist=True) as browser:
                page = browser.contexts[0].new_page()
                page.goto("https://example.com")
        """
        from ..lib.browser import _ensure_playwright, _cdp_url_for
        if framework != "playwright":
            raise SprntrlError(
                f"Unsupported framework {framework!r}. Only 'playwright' is supported in Python."
            )
        session = (
            self.wait_until_ready(session_id, timeout=wait_timeout)
            if wait
            else self.get(session_id)
        )
        if auto_whitelist:
            try:
                self._client._request(
                    "POST", "/api/v1/settings/ip-whitelist", json={"ip": "current"}
                )
            except Exception:
                pass
        sync_playwright = _ensure_playwright()
        pw = sync_playwright().start()
        browser = None
        try:
            browser = pw.chromium.connect_over_cdp(_cdp_url_for(self._client, session))
            yield browser
        finally:
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
            pw.stop()


class AsyncSessions:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client
        from .files import AsyncSessionFiles
        from .extensions import AsyncSessionExtensions
        self.files = AsyncSessionFiles(client)
        self.extensions = AsyncSessionExtensions(client)

    async def create(
        self,
        os: OS,
        location: str,
        *,
        persistent: bool = False,
        captcha_solver: bool = False,
        isolated_world: bool | None = None,
        headless: bool | None = None,
        block_images: bool = False,
        session_name: str | None = None,
        proxy: str | ProxyConfig | None = None,
        extensions: list[ExtensionInlineSpec] | None = None,
    ) -> Session:
        """Create a stealth browser session.

        See :py:meth:`Sessions.create` for details. Async equivalent.
        """
        body = _build_create_body(
            os, location,
            persistent=persistent,
            captcha_solver=captcha_solver,
            isolated_world=isolated_world,
            headless=headless,
            block_images=block_images,
            session_name=session_name,
            proxy=proxy,
            extensions=extensions,
        )
        return await self._client._request("POST", "/api/v1/sessions", json=body)

    async def list(self) -> list[Session]:
        resp = await self._client._request("GET", "/api/v1/sessions")
        return resp.get("sessions", [])

    async def list_active(self) -> list[Session]:
        resp = await self._client._request("GET", "/api/v1/sessions/active")
        return resp.get("sessions", [])

    async def list_history(self, *, page: int = 1, per_page: int = 25) -> PaginatedSessions:
        return await self._client._request(
            "GET",
            "/api/v1/sessions/history",
            params={"page": page, "per_page": per_page},
        )

    async def list_resumable(self, *, limit: int = 10) -> list[Session]:
        resp = await self._client._request(
            "GET", "/api/v1/sessions/resumable", params={"limit": limit}
        )
        return resp.get("sessions", [])

    async def list_persistent(self) -> list[Session]:
        """Persistent sessions (created with persistent=True), whether
        currently running or stopped-but-resumable."""
        resp = await self._client._request("GET", "/api/v1/sessions/persistent")
        return resp.get("sessions", [])

    async def list_locations(self) -> list[str]:
        resp = await self._client._request("GET", "/api/v1/sessions/locations")
        return resp.get("locations", [])

    async def get(self, session_id: str) -> Session:
        return await self._client._request("GET", f"/api/v1/sessions/{seg(session_id)}")

    async def stop(self, session_id: str) -> None:
        await self._client._request("DELETE", f"/api/v1/sessions/{seg(session_id)}")

    async def resume(
        self,
        session_id: str,
        *,
        proxy: str | ProxyConfig | None = None,
    ) -> Session:
        """Resume a stopped persistent session.

        Pass ``proxy`` to switch the session's proxy on resume. See the
        sync ``Sessions.resume`` docstring for the full contract.
        """
        body = _normalize_proxy(proxy)
        return await self._client._request(
            "POST",
            f"/api/v1/sessions/{seg(session_id)}/resume",
            json=body if body else None,
        )

    async def delete_persistent(self, session_id: str) -> None:
        await self._client._request(
            "DELETE", f"/api/v1/sessions/{seg(session_id)}/persist"
        )

    async def wait_until_ready(
        self,
        session_id: str,
        *,
        timeout: float = 60.0,
        poll_interval: float = 0.5,
    ) -> Session:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            session = await self.get(session_id)
            status = session.get("status")
            if status == "running":
                return session
            if status in ("failed", "stopped", "stopping"):
                raise SprntrlError(
                    f"Session {session_id} entered status {status!r} while waiting"
                )
            if loop.time() >= deadline:
                raise SprntrlError(
                    f"Session {session_id} not ready after {timeout}s (status={status!r})"
                )
            await asyncio.sleep(poll_interval)

    async def connect(
        self,
        session_id: str,
        *,
        framework: str = "playwright",
        auto_whitelist: bool = False,
        wait: bool = True,
        wait_timeout: float = 60.0,
    ) -> Any:
        from ..lib.browser import connect_async
        if wait:
            session = await self.wait_until_ready(session_id, timeout=wait_timeout)
        else:
            session = await self.get(session_id)
        return await connect_async(
            self._client, session, framework=framework, auto_whitelist=auto_whitelist
        )

    def cdp_url(self, session_id: str) -> str:
        """Return the CDP WebSocket URL for a session."""
        parsed = urlparse(self._client.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((
            scheme, parsed.netloc, f"/api/v1/sessions/{seg(session_id)}/cdp", "", "", "",
        ))

    @contextlib.asynccontextmanager
    async def browser_session(
        self,
        session_id: str,
        *,
        framework: str = "playwright",
        auto_whitelist: bool = False,
        wait: bool = True,
        wait_timeout: float = 60.0,
    ) -> AsyncIterator[Any]:
        """Async context manager that connects a browser and tears everything down on exit.

            async with client.sessions.browser_session(sid, auto_whitelist=True) as browser:
                page = await browser.contexts[0].new_page()
                await page.goto("https://example.com")
        """
        from ..lib.browser import _ensure_playwright_async, _cdp_url_for
        if framework != "playwright":
            raise SprntrlError(
                f"Unsupported framework {framework!r}. Only 'playwright' is supported in Python."
            )
        session = (
            await self.wait_until_ready(session_id, timeout=wait_timeout)
            if wait
            else await self.get(session_id)
        )
        if auto_whitelist:
            try:
                await self._client._request(
                    "POST", "/api/v1/settings/ip-whitelist", json={"ip": "current"}
                )
            except Exception:
                pass
        async_playwright = _ensure_playwright_async()
        pw = await async_playwright().start()
        browser = None
        try:
            browser = await pw.chromium.connect_over_cdp(_cdp_url_for(self._client, session))
            yield browser
        finally:
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass
            await pw.stop()
