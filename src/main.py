from src.routers.movies import router as movies_router
from fastapi import FastAPI
from src.routers.orders import router as orders_router

app = FastAPI()

app.include_router(movies_router)
app.include_router(orders_router)
