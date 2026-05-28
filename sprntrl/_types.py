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


class ProxySummary(TypedDict, total=False):
    """Display-friendly view of a session's proxy. Present only for BYO
    (bring-your-own) proxies — pool proxies are shared infra and the API
    deliberately hides their host/port. The password is never returned."""

    protocol: str
    host: str
    port: int
    username: str
    address: str  # convenience form: protocol://host:port


class Session(TypedDict, total=False):
    id: str
    user_id: str
    profile_id: str | None
    container_id: str | None
    chrome_port: int | None
    status: SessionStatus
    persistent: bool
    captcha_solver: bool
    session_name: str | None
    data_dir_path: str | None
    data_dir_size: int
    storage_status: str
    os: OS
    location: str
    started_at: str | None
    stopped_at: str | None
    created_at: str
    cdp_url: str
    uptime_seconds: int
    sidecar_port: int
    proxy: ProxySummary  # present only for BYO-proxy sessions


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
    allow_hours_overage: bool
    profile_count: int
    max_profiles: int
    bandwidth_rate_cents: int  # pool-proxy bandwidth, cents per GB
    hours_overage_rate_cents: int  # cents per hour over plan minutes
    bandwidth_bytes: int  # pool-proxy bytes consumed this period
    bandwidth_charge_amount_cents: int  # accrued bandwidth overage, cents
    hours_overage_minutes: int  # minutes used beyond plan allowance
    hours_overage_amount_cents: int  # accrued hours-overage charge, cents


class UsageMonth(TypedDict):
    month: str
    total_minutes: int
    plan_minutes: int
    overage_minutes: int


AccountStatus = Literal["pending_verification", "pending_payment", "active"]


class User(TypedDict, total=False):
    id: str
    email: str
    name: str | None
    plan: str
    role: str
    allow_hours_overage: bool
    byo_proxy_only: bool  # account may only use BYO proxies (no pool proxy)
    bandwidth_rate_cents: int  # pool-proxy bandwidth, cents per GB
    hours_overage_rate_cents: int  # cents per hour over plan minutes
    must_change_password: bool
    email_verified: bool
    account_status: AccountStatus
    oauth_provider: str  # "google" | "github"; absent for password accounts
    created_at: str


class ChangePasswordResult(TypedDict, total=False):
    message: str
    # Fresh tokens — issued so a programmatic client can swap credentials
    # without a re-login. Absent for cookie/session-only flows.
    access_token: str
    refresh_token: str
    token_type: str


class FileInfo(TypedDict, total=False):
    name: str
    size: int
    modified: str


ExtensionSource = Literal["upload", "webstore", "crx_url"]


class SessionExtension(TypedDict, total=False):
    """One Chrome extension attached to a persistent session's profile."""

    id: str  # internal UUID — pass to set_enabled() / remove()
    user_id: str
    session_name: str
    extension_id: str  # 32-char chromium ID
    name: str
    version: str
    manifest_version: int
    permissions: list[str]
    host_permissions: list[str]
    source: ExtensionSource
    source_ref: str | None
    size_bytes: int
    sha256: str
    enabled: bool
    created_at: str
    updated_at: str


class ExtensionInlineSpec(TypedDict, total=False):
    """Inline extension spec for ephemeral sessions on
    ``sessions.create(extensions=...)``. Exactly one of ``upload_b64``,
    ``webstore_url``, or ``crx_url`` must be set per entry."""

    upload_b64: str  # base64-encoded ZIP or CRX bytes
    filename: str
    webstore_url: str  # chromewebstore.google.com URL or bare 32-char ID
    crx_url: str  # direct HTTPS URL to a .crx or .zip
