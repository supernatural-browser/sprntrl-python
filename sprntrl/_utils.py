from __future__ import annotations

from urllib.parse import quote


def seg(value: object) -> str:
    """Percent-encode a single URL path segment.

    Caller- or server-supplied values (session ids, filenames, profile ids,
    etc.) are interpolated into request paths. Without encoding, a value
    containing ``/``, ``..``, ``?`` or ``#`` could traverse to a different
    authenticated endpoint or inject a query/fragment — all with the API key
    attached. ``safe=""`` ensures even ``/`` is escaped so the value can only
    ever be a single segment. Mirrors the Node SDK's ``encodeURIComponent``.
    """
    return quote(str(value), safe="")
