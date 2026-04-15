from __future__ import annotations

from typing import Any, Literal, TypedDict


ProxyProtocol = Literal["HTTP", "HTTPS", "SOCKS5"]
SessionStatus = Literal["creating", "running", "stopping", "stopped", "failed", "archiving"]
OS = Literal["macos", "windows"]


class ProxyConfig(TypedDict, total=False):
    protocol: ProxyProtocol
    host: str
    port: int
    username: str
    password: str


class Session(TypedDict, total=False):
    id: str
    user_id: str
    profile_id: str | None
    container_id: str | None
    chrome_port: int | None
    status: SessionStatus
    persistent: bool
    session_name: str | None
    data_dir_path: str | None
    data_dir_size: int
    storage_status: str
    os: OS
    location: str
    proxy_protocol: str | None
    proxy_host: str | None
    proxy_port: int | None
    proxy_username: str | None
    started_at: str | None
    stopped_at: str | None
    created_at: str
    cdp_url: str
    uptime_seconds: int
    sidecar_port: int


class PaginatedSessions(TypedDict):
    sessions: list[Session]
    total: int
    page: int
    per_page: int


class Profile(TypedDict, total=False):
    id: str
    user_id: str
    name: str
    description: str | None
    os: str | None
    location: str | None
    persona: str | None
    config_json: Any
    template_id: str | None
    created_at: str
    updated_at: str


class Template(TypedDict, total=False):
    id: str
    name: str
    os: str
    config: Any


class IPWhitelistEntry(TypedDict, total=False):
    id: str
    user_id: str
    ip_address: str
    label: str | None
    created_at: str


class APIKey(TypedDict, total=False):
    id: str
    name: str
    key_prefix: str
    last_used_at: str | None
    created_at: str
    revoked_at: str | None


class APIKeyCreated(APIKey, total=False):
    key: str  # Only present once at creation time


class Usage(TypedDict, total=False):
    total_minutes: int
    plan_minutes: int
    overage_minutes: int
    month: str
    plan: str
    usage_percentage: float
    profile_count: int
    max_profiles: int
    bandwidth_bytes: int
    bandwidth_limit_gb: int
    bandwidth_overage_rate_cents: int
    allow_bandwidth_overage: bool
    bandwidth_overage_bytes: int
    bandwidth_overage_amount_cents: int


class UsageMonth(TypedDict):
    month: str
    total_minutes: int
    plan_minutes: int
    overage_minutes: int


class User(TypedDict, total=False):
    id: str
    email: str
    name: str
    plan: str
    role: str
    byo_proxy: bool
    allow_bandwidth_overage: bool
    bandwidth_overage_rate_cents: int
    created_at: str


class FileInfo(TypedDict, total=False):
    name: str
    size: int
    modified: str
