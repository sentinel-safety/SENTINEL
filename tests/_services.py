# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

SERVICES: Final[tuple[tuple[str, str], ...]] = (
    ("services.gateway.app.main", "sentinel-gateway"),
    ("services.ingestion.app.main", "sentinel-ingestion"),
    ("services.preprocessing.app.main", "sentinel-preprocessing"),
    ("services.classifier_first_pass.app.main", "sentinel-classifier-first-pass"),
    ("services.scoring.app.main", "sentinel-scoring"),
    ("services.memory.app.main", "sentinel-memory"),
    ("services.graph.app.main", "sentinel-graph"),
    ("services.patterns.app.main", "sentinel-patterns"),
    ("services.response.app.main", "sentinel-response"),
    ("services.explainability.app.main", "sentinel-explainability"),
    ("services.honeypot.app.main", "sentinel-honeypot"),
    ("services.federation.app.main", "sentinel-federation"),
    ("services.synthetic_data.app.main", "sentinel-synthetic-data"),
    ("services.dashboard_bff.app.main", "sentinel-dashboard-bff"),
)
