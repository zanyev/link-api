from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AssociatedItem(BaseModel):
    id: int
    business_id: Optional[str] = None
    name: Optional[str] = None
    brand_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    unit_type: Optional[str] = None


class SearchItemResult(BaseModel):
    id: int
    business_id: Optional[str] = None
    name: Optional[str] = None
    brand_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    unit_type: Optional[str] = None
    distance: Optional[float] = None
    cluster_ids: List[int] = Field(default_factory=list)
    associated_items: Dict[int, List[AssociatedItem]] = Field(default_factory=dict)


class SearchItemsResponse(BaseModel):
    results: List[SearchItemResult]
