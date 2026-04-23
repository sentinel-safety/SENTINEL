# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        dict[str, Any]: JSONB().with_variant(JSON(), "sqlite"),
        list[Any]: JSONB().with_variant(JSON(), "sqlite"),
        UUID: PgUUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
