from __future__ import annotations

from ._base_client import SyncClient, AsyncClient
from .resources import (
    Sessions,
    AsyncSessions,
    Profiles,
    AsyncProfiles,
    Templates,
    AsyncTemplates,
    IPWhitelist,
    AsyncIPWhitelist,
    Usage,
    AsyncUsage,
    User,
    AsyncUser,
    APIKeys,
    AsyncAPIKeys,
)


class Sprntrl(SyncClient):
    """Sync Sprntrl SDK client.

    Usage:
        with Sprntrl() as client:
            session = client.sessions.create(os="macos", location="America/New_York")
            client.sessions.wait_until_ready(session["id"])
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sessions = Sessions(self)
        self.profiles = Profiles(self)
        self.templates = Templates(self)
        self.ip_whitelist = IPWhitelist(self)
        self.usage = Usage(self)
        self.user = User(self)
        self.api_keys = APIKeys(self)


class AsyncSprntrl(AsyncClient):
    """Async Sprntrl SDK client.

    Usage:
        async with AsyncSprntrl() as client:
            session = await client.sessions.create(os="macos", location="America/New_York")
            await client.sessions.wait_until_ready(session["id"])
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sessions = AsyncSessions(self)
        self.profiles = AsyncProfiles(self)
        self.templates = AsyncTemplates(self)
        self.ip_whitelist = AsyncIPWhitelist(self)
        self.usage = AsyncUsage(self)
        self.user = AsyncUser(self)
        self.api_keys = AsyncAPIKeys(self)
