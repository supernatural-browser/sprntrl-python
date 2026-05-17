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

session = client.sessions.create(os="macos", location="us-east")

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
        session = await client.sessions.create(os="macos", location="us-east")
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

- `client.sessions` — create, list, list_active, list_history, list_resumable, list_locations, get, stop, resume, delete_persistent, wait_until_ready, connect, browser_session, cdp_url
- `client.sessions.files` — list, download, upload
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
    client.sessions.create(os="macos", location="us-east")
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
