# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.graph.cypher import build_cypher_sql

pytestmark = pytest.mark.unit


def test_build_cypher_sql_wraps_query_with_return_shape() -> None:
    sql = build_cypher_sql(
        "MATCH (a:Actor) WHERE a.tenant_id = $tid RETURN count(a) AS n",
        return_columns=("n",),
    )
    assert "ag_catalog.cypher" in sql
    assert "'sentinel_graph'" in sql
    assert "(n agtype)" in sql
    assert "MATCH (a:Actor)" in sql


def test_build_cypher_sql_supports_multiple_columns() -> None:
    sql = build_cypher_sql(
        "MATCH (a:Actor) RETURN a.actor_id AS aid, a.tenant_id AS tid",
        return_columns=("aid", "tid"),
    )
    assert "(aid agtype, tid agtype)" in sql


def test_build_cypher_sql_rejects_empty_columns() -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_cypher_sql("MATCH (a) RETURN a", return_columns=())
