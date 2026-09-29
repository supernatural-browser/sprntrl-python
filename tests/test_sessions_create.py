import asyncio

import pytest

from sprntrl.resources.sessions import AsyncSessions, Sessions


class _SyncStub:
    def __init__(self):
        self.calls = []

    def _request(self, method, path, **kw):
        self.calls.append((method, path, kw))
        return {}


class _AsyncStub(_SyncStub):
    async def _request(self, method, path, **kw):
        self.calls.append((method, path, kw))
        return {}


NEW_FIELDS = ("country", "disable_geolocation", "proxy_relay", "fingerprint_overrides")


def _body(kwargs, *, use_async=False):
    if use_async:
        stub = _AsyncStub()
        asyncio.run(AsyncSessions(stub).create(**kwargs))
    else:
        stub = _SyncStub()
        Sessions(stub).create(**kwargs)
    (method, path, kw), = stub.calls
    assert (method, path) == ("POST", "/api/v1/sessions")
    return kw["json"]


@pytest.mark.parametrize("use_async", [False, True])
def test_new_fields_omitted_when_unset(use_async):
    body = _body({"os": "macos", "location": "America/New_York"}, use_async=use_async)
    assert body == {"os": "macos", "location": "America/New_York", "persistent": False}
    for f in NEW_FIELDS:
        assert f not in body


@pytest.mark.parametrize("use_async", [False, True])
def test_new_fields_serialized(use_async):
    overrides = {"userAgent": "x", "screen": {"width": 412}}
    body = _body(
        {
            "os": "android",
            "country": "GB",
            "disable_geolocation": True,
            "proxy_relay": True,
            "fingerprint_overrides": overrides,
        },
        use_async=use_async,
    )
    assert body == {
        "os": "android",
        "persistent": False,
        "country": "GB",
        "disable_geolocation": True,
        "proxy_relay": True,
        "fingerprint_overrides": overrides,
    }
    assert "location" not in body


def test_proxy_relay_false_is_sent_explicitly():
    body = _body({"os": "windows", "location": "Europe/London", "proxy_relay": False})
    assert body["proxy_relay"] is False
