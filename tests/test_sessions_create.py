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


NEW_FIELDS = ("country",)


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
    body = _body(
        {
            "os": "android",
            "country": "GB",
        },
        use_async=use_async,
    )
    assert body == {
        "os": "android",
        "persistent": False,
        "country": "GB",
    }
    assert "location" not in body

