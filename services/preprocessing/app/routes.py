# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import APIRouter

from services.preprocessing.app.features import extract_features
from shared.contracts.preprocess import PreprocessRequest, PreprocessResponse

router = APIRouter(prefix="/internal", tags=["preprocess"])


@router.post("/preprocess", response_model=PreprocessResponse)
def preprocess(payload: PreprocessRequest) -> PreprocessResponse:
    features = extract_features(
        event=payload.event,
        content=payload.content,
        recipient_age_bands=payload.recipient_age_bands,
        recipient_timezone=payload.recipient_timezone,
    )
    return PreprocessResponse(features=features)
