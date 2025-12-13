from endpoints.api import api_router
from fastapi import FastAPI

app = FastAPI(
    title="Linking Service",
    version="1.0.0",
)

app.include_router(api_router)
