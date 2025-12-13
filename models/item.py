from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Numeric
from typing import TYPE_CHECKING, Optional

from .base import BaseCreated, BaseTable

if TYPE_CHECKING:
    from .item_cluster import ItemCluster


class BaseRawItem(SQLModel):
    business_id: str
    name: str
    brand_name: str
    description: str

    price: Decimal = Field(
        sa_column=Column(Numeric(7, 2))
    )

    stock: Optional[int] = None
    category: Optional[str] = None
    unit_type: Optional[str] = None


class RawItemCreate(BaseRawItem, BaseCreated):
    pass

class RawItem(BaseRawItem, BaseCreated, BaseTable, table=True):
    __tablename__ = "raw_item"

    item_cluster: Optional["ItemCluster"] = Relationship(
        back_populates="raw_items"
    )
