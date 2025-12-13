from typing import Annotated, Generator

from core.database import engine
from fastapi import Depends
from sqlmodel import Session


def get_db() -> Generator:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
