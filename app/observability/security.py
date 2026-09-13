from fastapi import Request, Response
from starlette.responses import JSONResponse

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def csrf_middleware(request: Request, call_next):
    settings = request.app.state.settings
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if (
        settings.csrf_enabled
        and request.method in UNSAFE_METHODS
        and (request.cookies.get("access_token") or request.cookies.get("refresh_token"))
        and (not csrf_cookie or csrf_header != csrf_cookie)
    ):
        return JSONResponse({"detail": "CSRF validation failed"}, status_code=403)
    return await call_next(request)


async def security_headers_middleware(request: Request, call_next) -> Response:
    response = await call_next(request)
    if request.app.state.settings.security_headers_enabled:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        path = getattr(getattr(request, "url", None), "path", "")
        if path in {"/docs", "/redoc"}:
            # FastAPI's documentation UI is served as HTML that references
            # Swagger/ReDoc assets hosted by their configured CDN and uses an
            # inline bootstrap script. Keep this exception limited to docs.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "frame-ancestors 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; frame-ancestors 'none'"
            )
        if request.app.state.settings.hsts_enabled:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
