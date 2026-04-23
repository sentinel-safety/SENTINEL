from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request

from sentinel import WebhookSignatureError, verify_webhook_signature

app = FastAPI()


@app.post("/sentinel/webhook")
async def receive(request: Request) -> dict[str, str]:
    secret = os.environ["SENTINEL_WEBHOOK_SECRET"]
    body = await request.body()
    header = request.headers.get("X-Sentinel-Signature", "")
    try:
        verify_webhook_signature(
            header=header,
            secret=secret,
            body=body,
            now=datetime.now(UTC),
            skew_seconds=300,
        )
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"status": "ok"}
