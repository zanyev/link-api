from sqlmodel import Field, SQLModel, Relationship
from typing import List, TYPE_CHECKING
from .base import BaseCreated, BaseTable, BaseExtID


if TYPE_CHECKING:
    from .item import RawItem   


class BaseItemCluster(SQLModel):
    raw_item_id: int = Field(foreign_key="raw_item.id")
    match_score: float | None = None

class ItemClusterCreate(BaseItemCluster, BaseCreated):
    pass

class ItemCluster(BaseItemCluster, BaseExtID, BaseCreated, BaseTable, table=True):
    __tablename__ = "item_cluster"

    raw_items: List["RawItem"] = Relationship(back_populates="item_cluster")