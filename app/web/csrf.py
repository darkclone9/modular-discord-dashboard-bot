from collections.abc import Awaitable, Callable

from core.config import Settings
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in SAFE_METHODS or request.url.path.startswith("/auth/discord/"):
            return await call_next(request)

        cookie_token = request.cookies.get(self.settings.csrf_cookie_name)
        header_token = request.headers.get("x-csrf-token")
        if not cookie_token or not header_token or cookie_token != header_token:
            return Response(status_code=status.HTTP_403_FORBIDDEN, content="CSRF token missing")
        return await call_next(request)
