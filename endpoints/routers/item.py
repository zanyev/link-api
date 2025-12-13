from fastapi import APIRouter
from fastapi import UploadFile, File
from services.item import ingest_items_csv
from models.base import BaseResponseOut

from endpoints.dependencies import SessionDep

router = APIRouter()


@router.post("/csv", response_model=BaseResponseOut)
async def ingest_items_csv_api(
    db: SessionDep, file: UploadFile = File(...),
) -> None:
    """
    Ingest items from uploaded CSV file.
    """
    ingest_items_csv(
        db=db,
        file=file
    )
    return BaseResponseOut(message="Items ingested successfully")
