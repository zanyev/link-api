from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Numeric
from decimal import Decimal
from pgvector.sqlalchemy import Vector

from .base import BaseCreated, BaseTable

if TYPE_CHECKING:
    from .item_cluster_snapshot import ItemClusterSnapshot


class BaseRawItem(SQLModel):
    business_id: str
    name: str
    brand_name: str
    description: str

    price: Decimal = Field(sa_column=Column(Numeric(7, 2)))

    stock: Optional[int] = None
    category: Optional[str] = None
    unit_type: Optional[str] = None

    name_description_embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(1536))
    )


class RawItem(
    BaseRawItem,
    BaseCreated,
    BaseTable,
    table=True
):
    __tablename__ = "raw_item"

    cluster_snapshots: List["ItemClusterSnapshot"] = Relationship(
        back_populates="raw_item"
    )
