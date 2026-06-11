# Supernatural Python SDK

Official Python client for the [Supernatural](https://supernatural.sh) stealth browser-as-a-service API.

## Installation

```bash
pip install sprntrl
# Optional: Playwright integration
pip install 'sprntrl[playwright]' && playwright install chromium
```

## Quick start

```python
from sprntrl import Sprntrl

client = Sprntrl()  # reads SPRNTRL_API_KEY from env

session = client.sessions.create(os="macos", location="America/New_York")

# browser_session is a context manager that waits for the session,
# connects Playwright, and closes the browser + Playwright on exit.
# auto_whitelist=True registers your IP (CDP access is IP-gated).
with client.sessions.browser_session(session["id"], auto_whitelist=True) as browser:
    page = browser.contexts[0].new_page()
    page.goto("https://bot.sannysoft.com")
    page.screenshot(path="out.png")

client.sessions.stop(session["id"])
```

### Async

```python
import asyncio
from sprntrl import AsyncSprntrl

async def main():
    async with AsyncSprntrl() as client:
        session = await client.sessions.create(os="macos", location="America/New_York")
        async with client.sessions.browser_session(session["id"], auto_whitelist=True) as browser:
            page = await browser.contexts[0].new_page()
            await page.goto("https://example.com")
        await client.sessions.stop(session["id"])

asyncio.run(main())
```

### Lower-level `connect()` and `cdp_url()`

If you want to manage the browser lifecycle yourself:

```python
browser = client.sessions.connect(session_id, auto_whitelist=True)
# ... your code ...
browser.close()
```

Or to hand the raw WebSocket URL to any CDP client (chrome-remote-interface-python, raw `websockets`, etc.):

```python
url = client.sessions.cdp_url(session_id)
# url = "wss://api.supernatural.sh/api/v1/sessions/<id>/cdp"
```

## Session options

`sessions.create(os, location, ...)` takes `os` (`"macos"` | `"windows"`) and `location` (IANA timezone), plus:

- `persistent` + `session_name` — keep the browser profile across stop/resume (see below).
- `captcha_solver` — auto-solves hCaptcha, Turnstile, reCAPTCHA and more; billed per solve.
- `isolated_world` — default `True`: automation runs in a V8 world hidden from the page. Keep it on for stealth — pass `False` only if you must access page JS globals (main-world execution is detectable).
- `headless` — default **`True`** for API/SDK callers. Pass `False` to get the live browser view in the dashboard.
- `block_images` — default `False`. Disables image loading session-wide; cuts bandwidth and speeds up loads.
- `label` — pins the proxy-pool match to a specific pool row at `location` (one of the labels from `list_locations()`, e.g. `"Kentucky, US"`). Ignored for BYO-proxy sessions.
- `proxy` — bring your own proxy as a URL string (`"socks5://user:pass@host:1080"`) or dict (`{"protocol": ..., "host": ..., "port": ..., "username": ..., "password": ...}`). HTTP/HTTPS/SOCKS5.
- `extensions` — inline Chrome extensions for ephemeral sessions (see below).

### Locations

```python
locs = client.sessions.list_locations()
# {"options": [{"label": "Kentucky, US", "location": "America/New_York"}, ...],
#  "accepts_iana": True, "iana_examples": ["America/New_York", ...]}
```

Pool users must pick `location` (and optionally `label`) from `options`. `accepts_iana: True` means BYO-proxy users may pass any IANA timezone as `location` instead.

## Persistent sessions (profiles)

Create with `persistent=True` to keep the browser profile (cookies, storage, fingerprint) across runs:

```python
session = client.sessions.create(
    os="macos", location="America/New_York",
    persistent=True, session_name="my-profile",
)
# ... use it ...
client.sessions.stop(session["id"])

# Later: relaunch with the same identity. All overrides optional —
# omitted values keep what's stored on the profile.
session = client.sessions.resume(session["id"], headless=False)

# Done with the profile entirely:
client.sessions.delete_persistent(session["id"])
```

`resume()` accepts `os`, `location`, `label`, `captcha_solver`, `isolated_world`, `headless`, `block_images`, and `proxy` overrides. Changing `os` or `location` rebuilds the profile's pinned fingerprint — an intentional one-time identity drift; changing `location` on a pool session also re-assigns the pool proxy for the new region. Supplying `proxy` switches a pool session to BYO — switching BYO back to pool is not supported (delete + recreate).

## Files

Move files in and out of a running session:

```python
client.sessions.files.upload(sid, "input.csv", open("input.csv", "rb"))
files = client.sessions.files.list(sid)
data = client.sessions.files.download(sid, "report.pdf")
```

Uploads are capped at 100 MB per request.

## Extensions

Ephemeral sessions take inline extensions at create — each spec sets exactly one of `webstore_url`, `crx_url`, or `upload_b64`:

```python
session = client.sessions.create(
    os="macos", location="America/New_York",
    extensions=[{"webstore_url": "https://chromewebstore.google.com/detail/..."}],
)
```

Persistent profiles manage extensions via the sub-resource instead, so the set survives stop/resume:

```python
ext = client.sessions.extensions.add(sid, webstore_url="...")  # or upload= / crx_url=
client.sessions.extensions.list(sid)
client.sessions.extensions.set_enabled(sid, ext["id"], False)
client.sessions.extensions.remove(sid, ext["id"])
```

Manifest V3 only (Chromium 148 dropped MV2); max 16 per profile; uploads capped at 50 MiB. Changes take effect at the next session start — stop + resume to apply.

## Configuration

| Env var            | Default                    |
|--------------------|----------------------------|
| `SPRNTRL_API_KEY`  | —                          |
| `SPRNTRL_BASE_URL` | `https://api.supernatural.sh`   |

Or override per client:

```python
client = Sprntrl(api_key="sk_...", base_url="https://api.supernatural.sh", timeout=30, max_retries=2)
```

## Resources

- `client.sessions` — create, list, list_active, list_history, list_resumable, list_persistent, list_locations, get, stop, resume, delete_persistent, wait_until_ready, connect, browser_session, cdp_url
- `client.sessions.files` — list, download, upload
- `client.sessions.extensions` — add, list, set_enabled, remove (persistent profiles)
- `client.profiles` — create, list, get, update, duplicate, delete
- `client.templates.list()`
- `client.ip_whitelist` — list, add, remove
- `client.usage` — current, history
- `client.user` — me, update, update_settings, change_password
- `client.api_keys` — list, create (full key returned ONCE), revoke

## Error handling

```python
from sprntrl import Sprntrl, APIError, RateLimitError, AuthenticationError

client = Sprntrl()
try:
    client.sessions.create(os="macos", location="America/New_York")
except RateLimitError as e:
    print("rate limited:", e.status, e.body)
except AuthenticationError:
    print("bad API key")
except APIError as e:
    print("api error:", e.status, e)
```

Transient errors (5xx, 429, 408, connection errors) are retried automatically up to `max_retries` times with exponential backoff.

## Gotchas

- **CDP access is IP-whitelist gated.** The WebSocket at `/api/v1/sessions/:id/cdp` does not accept bearer auth — instead, your public IP (as Cloudflare sees it) must be in your account's whitelist. Use `client.ip_whitelist.add("current")` or pass `auto_whitelist=True` to `sessions.connect`.
- **Sessions start async.** `sessions.create` returns immediately with `status: "creating"`. Call `sessions.wait_until_ready(id)` before connecting, or just use `sessions.connect()` which waits for you.
- **API key is shown only once.** `api_keys.create()` returns the full `key` field exactly once — store it immediately.

## License

MIT
