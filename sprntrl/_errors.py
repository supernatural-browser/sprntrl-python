from __future__ import annotations

from typing import Any


class SprntrlError(Exception):
    pass


class APIError(SprntrlError):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        # NOTE: the live httpx.Response is deliberately NOT retained. Its
        # `.request.headers` carries `Authorization: ApiKey <key>`, so keeping
        # it here would leak the API key into any log/Sentry capture of the
        # exception. Only the status code and the parsed (server-controlled)
        # error body are exposed.
        self.body = body


class BadRequestError(APIError): pass
class AuthenticationError(APIError): pass
class PermissionDeniedError(APIError): pass
class NotFoundError(APIError): pass
class ConflictError(APIError): pass
class UnprocessableEntityError(APIError): pass
class RateLimitError(APIError): pass
class InternalServerError(APIError): pass


class APIConnectionError(APIError):
    def __init__(self, message: str = "Connection error", *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class APIConnectionTimeoutError(APIConnectionError):
    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)


_STATUS_MAP: dict[int, type[APIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def error_for_status(status: int, message: str, *, body: Any = None) -> APIError:
    if status >= 500:
        cls = InternalServerError
    else:
        cls = _STATUS_MAP.get(status, APIError)
    return cls(message, status=status, body=body)
