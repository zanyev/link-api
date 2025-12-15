import uuid
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional

from .base import BaseCreated, BaseTable

if TYPE_CHECKING:
    from .item import RawItem


class ItemClusterSnapshotBase(SQLModel):
    cluster_run_id: uuid.UUID = Field(index=True)

    cluster_id: int = Field(index=True)

    raw_item_id: int = Field(
        foreign_key="raw_item.id",
        index=True
    )


class ItemClusterSnapshot(
    ItemClusterSnapshotBase,
    BaseCreated,
    BaseTable,
    table=True
):
    __tablename__ = "item_cluster_snapshot"

    raw_item: Optional["RawItem"] = Relationship(
        back_populates="cluster_snapshots"
    )
