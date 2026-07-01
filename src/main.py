from src.routers.movies import router as movies_router
from fastapi import FastAPI

app = FastAPI()

app.include_router(movies_router)
