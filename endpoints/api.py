from fastapi import APIRouter

from endpoints.routers import item

api_router = APIRouter()

api_router.include_router(item.router, tags=["item"], prefix="/item")
