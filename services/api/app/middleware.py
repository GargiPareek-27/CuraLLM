"""Request context middleware: request ids and metadata-only access logs."""
import logging
import time

from app.request_id import resolve_request_id

logger = logging.getLogger("curallm.access")


async def request_context_middleware(request, call_next):
    request_id = resolve_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Log the exception type only: messages can contain user input.
        logger.error("unhandled_error request_id=%s exc=%s", request_id, type(exc).__name__)
        raise
    duration_ms = (time.perf_counter() - started) * 1000
    # Method, path and status only. Never log bodies or query strings.
    logger.info(
        "request request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response
