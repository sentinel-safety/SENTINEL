# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.graph.views import ContactGraphView

_SEARCH_PATH = "SET search_path = ag_catalog, public"
_MINOR_BANDS = ("under_13", "13_15", "16_17")


@dataclass
class ContactEdgeRepository:
    session: AsyncSession

    async def record_interaction(
        self,
        *,
        tenant_id: UUID,
        source_actor_id: UUID,
        target_actor_id: UUID,
        occurred_at: datetime,
        target_age_band: str,
    ) -> None:
        await self.session.execute(text(_SEARCH_PATH))
        tenant = str(tenant_id)
        source = str(source_actor_id)
        target = str(target_actor_id)
        ts = occurred_at.isoformat()
        await self.session.execute(
            text(_build_merge_cypher(tenant=tenant, source=source, target=target))
        )
        await self.session.execute(
            text(
                _build_upsert_cypher(
                    tenant=tenant,
                    source=source,
                    target=target,
                    ts=ts,
                    age_band=target_age_band,
                )
            )
        )

    async def get_contact_graph(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        now: datetime,
        lookback_days: int,
    ) -> ContactGraphView:
        await self.session.execute(text(_SEARCH_PATH))
        tenant = str(tenant_id)
        actor = str(actor_id)
        since_iso = (now - timedelta(days=lookback_days)).isoformat()

        total = await self._scalar_int(_build_total_cypher(tenant=tenant, actor=actor))
        minor_count = await self._scalar_int(
            _build_minor_cypher(tenant=tenant, actor=actor, since_iso=since_iso)
        )
        distribution = await self._age_band_distribution(tenant=tenant, actor=actor)

        velocity = total / float(lookback_days) if lookback_days else 0.0

        return ContactGraphView(
            distinct_contacts_total=total,
            distinct_minor_contacts_window=minor_count,
            contact_velocity_per_day=velocity,
            age_band_distribution=distribution,
            lookback_days=lookback_days,
        )

    async def _scalar_int(self, sql: str) -> int:
        row = await self.session.execute(text(sql))
        return _agtype_to_int(row.scalar_one())

    async def _age_band_distribution(self, *, tenant: str, actor: str) -> dict[str, int]:
        result = await self.session.execute(
            text(_build_distribution_cypher(tenant=tenant, actor=actor))
        )
        distribution: dict[str, int] = {}
        for row in result.all():
            band = _agtype_to_band(row.band)
            distribution[band] = distribution.get(band, 0) + _agtype_to_int(row.n)
        return distribution


def _agtype_to_int(value: Any) -> int:
    if value is None:
        return 0
    stripped = str(value).strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
    return int(stripped)


def _agtype_to_band(value: Any) -> str:
    if value is None:
        return "unknown"
    stripped = str(value).strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
    return stripped or "unknown"


def _build_merge_cypher(*, tenant: str, source: str, target: str) -> str:
    cypher = (
        f"MERGE (a:Actor {{tenant_id: '{tenant}', actor_id: '{source}'}}) "
        f"MERGE (b:Actor {{tenant_id: '{tenant}', actor_id: '{target}'}}) "
        "MERGE (a)-[r:INTERACTED_WITH]->(b) "
        "RETURN r"
    )
    return f"SELECT * FROM ag_catalog.cypher('sentinel_graph', $$ {cypher} $$) AS (r agtype)"  # noqa: S608


def _build_upsert_cypher(*, tenant: str, source: str, target: str, ts: str, age_band: str) -> str:
    cypher = (
        f"MATCH (a:Actor {{tenant_id: '{tenant}', actor_id: '{source}'}})"
        f"-[r:INTERACTED_WITH]->"
        f"(b:Actor {{tenant_id: '{tenant}', actor_id: '{target}'}}) "
        f"SET r.tenant_id = '{tenant}', "
        f"r.first_at = COALESCE(r.first_at, '{ts}'), "
        f"r.last_at = '{ts}', "
        "r.count = COALESCE(r.count, 0) + 1, "
        f"r.minor_age_band_flag = COALESCE(r.minor_age_band_flag, '{age_band}') "
        "RETURN r.count"
    )
    return f"SELECT * FROM ag_catalog.cypher('sentinel_graph', $$ {cypher} $$) AS (c agtype)"  # noqa: S608


def _build_total_cypher(*, tenant: str, actor: str) -> str:
    cypher = (
        f"MATCH (a:Actor {{tenant_id: '{tenant}', actor_id: '{actor}'}})"
        "-[r:INTERACTED_WITH]->(b:Actor) "
        "RETURN count(DISTINCT b) AS n"
    )
    return f"SELECT * FROM ag_catalog.cypher('sentinel_graph', $$ {cypher} $$) AS (n agtype)"  # noqa: S608


def _build_minor_cypher(*, tenant: str, actor: str, since_iso: str) -> str:
    minor_clause = " OR ".join(f"r.minor_age_band_flag = '{band}'" for band in _MINOR_BANDS)
    cypher = (
        f"MATCH (a:Actor {{tenant_id: '{tenant}', actor_id: '{actor}'}})"
        "-[r:INTERACTED_WITH]->(b:Actor) "
        f"WHERE r.last_at >= '{since_iso}' AND ({minor_clause}) "
        "RETURN count(DISTINCT b) AS n"
    )
    return f"SELECT * FROM ag_catalog.cypher('sentinel_graph', $$ {cypher} $$) AS (n agtype)"  # noqa: S608


def _build_distribution_cypher(*, tenant: str, actor: str) -> str:
    cypher = (
        f"MATCH (a:Actor {{tenant_id: '{tenant}', actor_id: '{actor}'}})"
        "-[r:INTERACTED_WITH]->(b:Actor) "
        "RETURN r.minor_age_band_flag AS band, count(b) AS n"
    )
    return (
        "SELECT * FROM ag_catalog.cypher('sentinel_graph', "  # noqa: S608
        f"$$ {cypher} $$) AS (band agtype, n agtype)"
    )
