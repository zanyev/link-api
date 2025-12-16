from datetime import datetime
from typing import Generic , TypeVar

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, func, text
from sqlmodel import Field, SQLModel


T = TypeVar("T")

class BaseTable(SQLModel):
    """
    Base object that will be in every table creating id and created_at columns
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        nullable=False,
    )

class BaseCreated(SQLModel):
    created_by: str

class BaseUpdated(SQLModel):
    updated_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={"onupdate": func.now(), "nullable": True},  
    )
    updated_by: str | None = Field(default=None)

class BaseResponseOut(BaseModel, Generic[T]):
    message: str = Field("Response of what happened")
    result: T | None = None