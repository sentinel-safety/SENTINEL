# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

_GRAPH_NAME = "sentinel_graph"
_SEARCH_PATH = "SET search_path = ag_catalog, public"


def build_cypher_sql(query: str, *, return_columns: Sequence[str]) -> str:
    if not return_columns:
        raise ValueError("at least one return column is required")
    cols = ", ".join(f"{c} agtype" for c in return_columns)
    escaped = query.replace("$$", "$ $")
    return f"SELECT * FROM ag_catalog.cypher('{_GRAPH_NAME}', $${escaped}$$) AS ({cols})"  # noqa: S608


async def run_cypher(
    session: AsyncSession,
    query: str,
    *,
    return_columns: Sequence[str],
    params: dict[str, Any] | None = None,
) -> list[Row[Any]]:
    await session.execute(text(_SEARCH_PATH))
    sql = build_cypher_sql(query, return_columns=return_columns)
    result = await session.execute(text(sql), params or {})
    return list(result.all())
