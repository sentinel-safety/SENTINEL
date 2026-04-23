# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.observability import bind_request_id, clear_context

REQUEST_ID_HEADER = "x-request-id"


def coerce_request_id(raw: str | None) -> str:
    if raw is None:
        return str(uuid4())
    try:
        return str(UUID(raw))
    except ValueError:
        return str(uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = coerce_request_id(request.headers.get(REQUEST_ID_HEADER))
        bind_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            clear_context()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
