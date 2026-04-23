# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["meta"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/version")
def version(request: Request) -> dict[str, str]:
    return {
        "service": request.app.state.settings.service_name,
        "version": request.app.version,
        "environment": request.app.state.settings.env,
    }
