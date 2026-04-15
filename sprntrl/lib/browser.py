from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping
from urllib.parse import urlparse, urlunparse

from .._errors import SprntrlError

if TYPE_CHECKING:
    from .._base_client import SyncClient, AsyncClient


def _cdp_url_for(client: "SyncClient | AsyncClient", session: Mapping[str, Any]) -> str:
    """Build the CDP WebSocket URL from the client's base URL. The API proxies
    the WebSocket through /api/v1/sessions/:id/cdp with an IP-whitelist check —
    this path is what external callers must use. (The server also returns a
    cdp_url field, but that's an internal host:port that isn't reachable from
    outside the API host.)"""
    session_id = session["id"]
    parsed = urlparse(client.base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((
        scheme, parsed.netloc, f"/api/v1/sessions/{session_id}/cdp", "", "", "",
    ))


def _ensure_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise SprntrlError(
            "Playwright is not installed. Run `pip install playwright` "
            "(and `playwright install chromium` once)."
        ) from exc
    return sync_playwright


def _ensure_playwright_async() -> Any:
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError as exc:
        raise SprntrlError(
            "Playwright is not installed. Run `pip install playwright` "
            "(and `playwright install chromium` once)."
        ) from exc
    return async_playwright


def connect_sync(
    client: "SyncClient",
    session: Mapping[str, Any],
    *,
    framework: str = "playwright",
    auto_whitelist: bool = False,
) -> Any:
    if framework != "playwright":
        raise SprntrlError(
            f"Unsupported framework {framework!r}. Only 'playwright' is supported in Python."
        )
    if auto_whitelist:
        try:
            client._request(
                "POST", "/api/v1/settings/ip-whitelist", json={"ip": "current"}
            )
        except Exception:
            # Already-whitelisted or race; ignore — connect attempt will surface the real problem.
            pass

    cdp_url = _cdp_url_for(client, session)
    sync_playwright = _ensure_playwright()
    pw = sync_playwright().start()
    try:
        return pw.chromium.connect_over_cdp(cdp_url)
    except Exception:
        pw.stop()
        raise


async def connect_async(
    client: "AsyncClient",
    session: Mapping[str, Any],
    *,
    framework: str = "playwright",
    auto_whitelist: bool = False,
) -> Any:
    if framework != "playwright":
        raise SprntrlError(
            f"Unsupported framework {framework!r}. Only 'playwright' is supported in Python."
        )
    if auto_whitelist:
        try:
            await client._request(
                "POST", "/api/v1/settings/ip-whitelist", json={"ip": "current"}
            )
        except Exception:
            pass

    cdp_url = _cdp_url_for(client, session)
    async_playwright = _ensure_playwright_async()
    pw = await async_playwright().start()
    try:
        return await pw.chromium.connect_over_cdp(cdp_url)
    except Exception:
        await pw.stop()
        raise
